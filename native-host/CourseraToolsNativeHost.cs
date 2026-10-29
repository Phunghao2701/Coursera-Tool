using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using System.Web.Script.Serialization;

internal sealed class Credentials
{
    public string ClientId { get; set; }
    public string HostId { get; set; }
    public string Subject { get; set; }
    public string Name { get; set; }
    public string Email { get; set; }
    public string IdToken { get; set; }
    public string AccessToken { get; set; }
    public string RefreshToken { get; set; }
    public string Scope { get; set; }
    public long ExpiresAt { get; set; }
}

internal sealed class AuthorizationAttempt
{
    public string RequestId;
    public string State;
    public string Nonce;
    public string Verifier;
    public string RedirectUri;
    public string RequestedClientId;
    public string IdTokenHint;
    public string HostId;
}

internal static class CourseraToolsNativeHost
{
    private const string HostName = "com.coursera.tools.chatgpt";
    private const string Issuer = "https://auth.openai.com";
    private const string AuthorizationEndpoint = "https://auth.openai.com/api/accounts/authorize";
    private const string TokenEndpoint = "https://auth.openai.com/api/accounts/oauth/token";
    private const string JwksEndpoint = "https://auth.openai.com/.well-known/jwks.json";
    private const string Resource = "https://api.openai.com/v1";
    private const string CredentialFileName = "chatgpt-credentials.bin";
    private const string HostIdFileName = "chatgpt-host-id.txt";
    private static readonly JavaScriptSerializer Json = new JavaScriptSerializer { MaxJsonLength = 4 * 1024 * 1024, RecursionLimit = 64 };
    private static readonly object OutputLock = new object();
    private static readonly object StateLock = new object();
    private static volatile bool _authRunning;
    private static volatile bool _authCancelled;
    private static volatile bool _askRunning;
    private static volatile bool _quizCancelled;
    private static HttpWebRequest _activeInferenceRequest;

    private static int Main(string[] args)
    {
        ServicePointManager.SecurityProtocol = (SecurityProtocolType)3072;
        if (!HasExtensionCaller(args)) return 2;

        Stream input = Console.OpenStandardInput();
        while (true)
        {
            object message;
            try
            {
                message = ReadNativeMessage(input);
            }
            catch (Exception ex)
            {
                WriteError(null, "Invalid native message: " + ex.Message);
                return 3;
            }

            if (message == null) return 0;
            try
            {
                HandleMessage(ToDictionary(message));
            }
            catch (Exception ex)
            {
                Dictionary<string, object> parsed = message as Dictionary<string, object>;
                WriteError(parsed == null ? null : GetString(parsed, "requestId"), SafeMessage(ex));
            }
        }
    }

    private static bool HasExtensionCaller(string[] args)
    {
        if (args == null) return false;
        foreach (string arg in args)
        {
            if (arg != null && arg.StartsWith("chrome-extension://", StringComparison.OrdinalIgnoreCase)) return true;
        }
        return false;
    }

    private static void HandleMessage(Dictionary<string, object> message)
    {
        string requestId = GetString(message, "requestId");
        string action = GetString(message, "action");
        if (String.IsNullOrWhiteSpace(requestId) || requestId.Length > 100)
        {
            WriteError(requestId, "Missing or invalid request identifier.");
            return;
        }

        if (action == "status")
        {
            Credentials credentials = LoadCredentials();
            WriteMessage(new Dictionary<string, object>
            {
                { "requestId", requestId },
                { "type", "status" },
                { "connected", credentials != null && !String.IsNullOrWhiteSpace(credentials.AccessToken) && !String.IsNullOrWhiteSpace(credentials.RefreshToken) && HasPlanScope(credentials.Scope) },
                { "name", credentials == null ? "" : credentials.Name },
                { "email", credentials == null ? "" : credentials.Email }
            });
            return;
        }

        if (action == "sign_in")
        {
            lock (StateLock)
            {
                if (_authRunning)
                {
                    WriteError(requestId, "A ChatGPT sign-in is already in progress.");
                    return;
                }
                _authRunning = true;
                _authCancelled = false;
            }
            Thread thread = new Thread(delegate() { RunSignIn(requestId); });
            thread.IsBackground = true;
            thread.Start();
            return;
        }

        if (action == "cancel_sign_in")
        {
            _authCancelled = true;
            WriteMessage(new Dictionary<string, object> { { "requestId", requestId }, { "type", "sign_in_cancelled" } });
            return;
        }

        if (action == "sign_out")
        {
            CancelQuizRequest();
            DateTime cancelStarted = DateTime.UtcNow;
            while (_askRunning && (DateTime.UtcNow - cancelStarted).TotalSeconds < 40) Thread.Sleep(50);

            Credentials credentials = LoadCredentials();
            bool revoked = false;
            if (credentials != null && !String.IsNullOrWhiteSpace(credentials.RefreshToken))
            {
                try
                {
                    RevokeRefreshToken(credentials);
                    revoked = true;
                }
                catch { }
            }
            if (credentials != null) File.Delete(CredentialPath());
            WriteMessage(new Dictionary<string, object>
            {
                { "requestId", requestId },
                { "type", "signed_out" },
                { "revoked", revoked }
            });
            return;
        }

        if (action == "ask_quiz")
        {
            lock (StateLock)
            {
                if (_askRunning)
                {
                    WriteError(requestId, "A quiz request is already running.");
                    return;
                }
                _askRunning = true;
                _quizCancelled = false;
            }
            object questions;
            if (!message.TryGetValue("questions", out questions))
            {
                _askRunning = false;
                WriteError(requestId, "No quiz questions were provided.");
                return;
            }
            Thread thread = new Thread(delegate() { RunQuizRequest(requestId, questions); });
            thread.IsBackground = true;
            thread.Start();
            return;
        }

        if (action == "cancel_quiz")
        {
            CancelQuizRequest();
            WriteMessage(new Dictionary<string, object> { { "requestId", requestId }, { "type", "quiz_cancelled" } });
            return;
        }

        WriteError(requestId, "Unsupported native host action.");
    }

    private static void RunSignIn(string requestId)
    {
        TcpListener listener = null;
        try
        {
            Credentials existing = LoadCredentials();
            string hostId = LoadOrCreateHostId();
            string state = RandomToken(32);
            string nonce = RandomToken(32);
            string verifier = RandomToken(48);
            string challenge = Base64Url(SHA256.Create().ComputeHash(Encoding.ASCII.GetBytes(verifier)));

            listener = new TcpListener(IPAddress.Loopback, 0);
            listener.Start(1);
            int port = ((IPEndPoint)listener.LocalEndpoint).Port;
            string redirectUri = "http://127.0.0.1:" + port + "/auth/callback";

            AuthorizationAttempt attempt = new AuthorizationAttempt
            {
                RequestId = requestId,
                State = state,
                Nonce = nonce,
                Verifier = verifier,
                RedirectUri = redirectUri,
                RequestedClientId = existing == null ? "dynamic_agent_client" : existing.ClientId,
                IdTokenHint = existing == null ? null : existing.IdToken,
                HostId = hostId
            };

            string url = BuildAuthorizationUrl(attempt);
            WriteMessage(new Dictionary<string, object>
            {
                { "requestId", requestId },
                { "type", "auth_open" },
                { "url", url }
            });

            TcpClient client = WaitForCallback(listener, 300000);
            if (client == null) throw new InvalidOperationException("Sign-in timed out. Try again from the extension.");

            using (client)
            {
                using (NetworkStream stream = client.GetStream())
                using (StreamReader reader = new StreamReader(stream, Encoding.ASCII, false, 4096, true))
                {
                    string requestLine = reader.ReadLine();
                    if (String.IsNullOrWhiteSpace(requestLine))
                    {
                        WriteHttpResponse(stream, 400, "The sign-in callback was empty.");
                        throw new InvalidOperationException("The sign-in callback was empty.");
                    }

                    string line;
                    while (!String.IsNullOrEmpty(line = reader.ReadLine())) { }
                    string[] parts = requestLine.Split(' ');
                    if (parts.Length < 2 || !String.Equals(parts[0], "GET", StringComparison.OrdinalIgnoreCase))
                    {
                        WriteHttpResponse(stream, 405, "Only the OAuth callback is accepted.");
                        throw new InvalidOperationException("Unexpected request to the sign-in callback.");
                    }

                    Uri requestUri = new Uri(new Uri("http://127.0.0.1:" + ((IPEndPoint)listener.LocalEndpoint).Port), parts[1]);
                    if (!String.Equals(requestUri.AbsolutePath, "/auth/callback", StringComparison.Ordinal))
                    {
                        WriteHttpResponse(stream, 404, "This local endpoint only accepts the ChatGPT sign-in callback.");
                        throw new InvalidOperationException("Unexpected sign-in callback path.");
                    }

                    Dictionary<string, string> query = ParseQuery(requestUri.Query);
                    string returnedState = GetString(query, "state");
                    if (!FixedTimeEquals(state, returnedState))
                    {
                        WriteHttpResponse(stream, 400, "Sign-in could not be verified. Return to Coursera Tools and try again.");
                        throw new InvalidOperationException("The sign-in state did not match.");
                    }

                    string oauthError = GetString(query, "error");
                    if (!String.IsNullOrWhiteSpace(oauthError))
                    {
                        WriteHttpResponse(stream, 400, "ChatGPT sign-in was not completed. Return to Coursera Tools and try again.");
                        throw new InvalidOperationException(oauthError == "access_denied" ? "ChatGPT access was not approved." : "ChatGPT sign-in failed.");
                    }

                    string code = GetString(query, "code");
                    string callbackClientId = GetString(query, "client_id");
                    if (String.IsNullOrWhiteSpace(code))
                    {
                        WriteHttpResponse(stream, 400, "The sign-in response did not include an authorization code.");
                        throw new InvalidOperationException("The sign-in response did not include an authorization code.");
                    }

                    string clientId = attempt.RequestedClientId == "dynamic_agent_client" ? callbackClientId : attempt.RequestedClientId;
                    if (String.IsNullOrWhiteSpace(clientId) || clientId.Length > 256)
                    {
                        WriteHttpResponse(stream, 400, "The ChatGPT app registration was incomplete. Try signing in again.");
                        throw new InvalidOperationException("ChatGPT did not return an app registration identifier.");
                    }
                    if (attempt.RequestedClientId != "dynamic_agent_client" && !String.IsNullOrWhiteSpace(callbackClientId) && !String.Equals(callbackClientId, attempt.RequestedClientId, StringComparison.Ordinal))
                    {
                        WriteHttpResponse(stream, 400, "The ChatGPT account registration changed unexpectedly.");
                        throw new InvalidOperationException("The returned app registration did not match the saved registration.");
                    }

                    string tokenJson = PostForm(TokenEndpoint, new Dictionary<string, string>
                    {
                        { "grant_type", "authorization_code" },
                        { "client_id", clientId },
                        { "code", code },
                        { "code_verifier", verifier },
                        { "redirect_uri", redirectUri },
                        { "resource", Resource }
                    });
                    Dictionary<string, object> tokens = ParseObject(tokenJson);
                    string scope = GetString(tokens, "scope");
                    if (!HasPlanScope(scope))
                    {
                        WriteHttpResponse(stream, 400, "Sign-in succeeded, but ChatGPT plan usage was not approved. Reconnect and allow plan usage.");
                        throw new InvalidOperationException("ChatGPT plan usage was not approved. Reconnect and allow plan usage.");
                    }

                    string idToken = GetString(tokens, "id_token");
                    string accessToken = GetString(tokens, "access_token");
                    string refreshToken = GetString(tokens, "refresh_token");
                    if (String.IsNullOrWhiteSpace(idToken) || String.IsNullOrWhiteSpace(accessToken) || String.IsNullOrWhiteSpace(refreshToken))
                    {
                        WriteHttpResponse(stream, 400, "ChatGPT did not return the credentials needed for plan usage.");
                        throw new InvalidOperationException("ChatGPT did not return the required credentials.");
                    }

                    Dictionary<string, object> identity = ValidateIdToken(idToken, clientId, nonce);
                    string subject = GetString(identity, "sub");
                    if (existing != null && !String.Equals(existing.Subject, subject, StringComparison.Ordinal))
                    {
                        WriteHttpResponse(stream, 400, "This connection belongs to a different ChatGPT account. Disconnect first, then sign in again.");
                        throw new InvalidOperationException("The ChatGPT account changed. Disconnect before switching accounts.");
                    }

                    Credentials credentials = new Credentials
                    {
                        ClientId = clientId,
                        HostId = hostId,
                        Subject = subject,
                        Name = GetString(identity, "name"),
                        Email = GetString(identity, "email"),
                        IdToken = idToken,
                        AccessToken = accessToken,
                        RefreshToken = refreshToken,
                        Scope = scope,
                        ExpiresAt = UnixNow() + GetInt(tokens, "expires_in", 3600)
                    };
                    SaveCredentials(credentials);
                    WriteHttpResponse(stream, 200, "ChatGPT is connected to Coursera Tools. You can close this tab and return to the extension.");
                    WriteMessage(new Dictionary<string, object>
                    {
                        { "requestId", requestId },
                        { "type", "auth_result" },
                        { "success", true },
                        { "name", credentials.Name },
                        { "email", credentials.Email }
                    });
                }
            }
        }
        catch (Exception ex)
        {
            WriteMessage(new Dictionary<string, object>
            {
                { "requestId", requestId },
                { "type", "auth_result" },
                { "success", false },
                { "error", SafeMessage(ex) }
            });
        }
        finally
        {
            if (listener != null) listener.Stop();
            _authRunning = false;
            _authCancelled = false;
        }
    }

    private static TcpClient WaitForCallback(TcpListener listener, int timeoutMilliseconds)
    {
        DateTime started = DateTime.UtcNow;
        while (!_authCancelled && (DateTime.UtcNow - started).TotalMilliseconds < timeoutMilliseconds)
        {
            if (listener.Pending()) return listener.AcceptTcpClient();
            Thread.Sleep(100);
        }
        if (_authCancelled) throw new InvalidOperationException("ChatGPT sign-in was cancelled.");
        return null;
    }

    private static string BuildAuthorizationUrl(AuthorizationAttempt attempt)
    {
        string scopes = "openid profile email offline_access resource.invoke chatgpt.tokens.use.direct";
        List<string> query = new List<string>
        {
            "client_id=" + Url(attempt.RequestedClientId),
            "response_type=code",
            "redirect_uri=" + Url(attempt.RedirectUri),
            "scope=" + Url(scopes),
            "resource=" + Url(Resource),
            "state=" + Url(attempt.State),
            "nonce=" + Url(attempt.Nonce),
            "code_challenge_method=S256",
            "code_challenge=" + Url(Base64Url(SHA256.Create().ComputeHash(Encoding.ASCII.GetBytes(attempt.Verifier))))
        };

        query.Add("ext_agent_host_id=" + Url(attempt.HostId));
        if (attempt.RequestedClientId == "dynamic_agent_client")
        {
            query.Add("agent_name_hint=" + Url("Coursera Tools"));
        }
        else if (!String.IsNullOrWhiteSpace(attempt.IdTokenHint))
        {
            query.Add("id_token_hint=" + Url(attempt.IdTokenHint));
        }

        return AuthorizationEndpoint + "?" + String.Join("&", query.ToArray());
    }

    private static void RunQuizRequest(string requestId, object rawQuestions)
    {
        try
        {
            ThrowIfQuizCancelled();
            string prompt = BuildQuizPrompt(rawQuestions);
            ThrowIfQuizCancelled();
            Credentials credentials = LoadCredentials();
            if (credentials == null || !HasPlanScope(credentials.Scope)) throw new InvalidOperationException("Connect ChatGPT and allow plan usage before using Quiz AI.");

            credentials = EnsureFreshCredentials(credentials);
            ThrowIfQuizCancelled();
            string model = GetFirstVisibleModel(credentials.AccessToken);
            string output = RunResponsesRequest(credentials.AccessToken, model, prompt);
            ThrowIfQuizCancelled();
            WriteMessage(new Dictionary<string, object>
            {
                { "requestId", requestId },
                { "type", "quiz_result" },
                { "success", true },
                { "text", output }
            });
        }
        catch (Exception ex)
        {
            WriteMessage(new Dictionary<string, object>
            {
                { "requestId", requestId },
                { "type", "quiz_result" },
                { "success", false },
                { "error", SafeMessage(ex) }
            });
        }
        finally
        {
            _askRunning = false;
        }
    }

    private static string BuildQuizPrompt(object rawQuestions)
    {
        object[] questions = rawQuestions as object[];
        if (questions == null || questions.Length == 0 || questions.Length > 25) throw new InvalidOperationException("The page did not contain a supported quiz with 1 to 25 questions.");

        StringBuilder prompt = new StringBuilder();
        prompt.AppendLine("Answer the following course practice questions using the question text and choices. If the provided information is insufficient, say so in the explanation and return no choices for that question.");
        prompt.AppendLine("Return only valid JSON with this shape: {\"answers\":[{\"question\":1,\"choices\":[1],\"text\":\"optional short answer\",\"explanation\":\"brief reason\"}]}.");
        prompt.AppendLine("Choice numbers are 1-based and must refer to the listed choices. For a single-choice question return one choice; for multi-select return every selected choice. Do not include markdown fences.");
        prompt.AppendLine();

        for (int i = 0; i < questions.Length; i++)
        {
            Dictionary<string, object> question = ToDictionary(questions[i]);
            string stem = BoundText(GetString(question, "stem"), 2500);
            if (String.IsNullOrWhiteSpace(stem)) continue;
            prompt.Append("Question ").Append(i + 1).Append(" [").Append(BoundText(GetString(question, "kind"), 40)).AppendLine("]:");
            prompt.AppendLine(stem);
            object[] options = GetArray(question, "options");
            if (options != null)
            {
                for (int optionIndex = 0; optionIndex < options.Length && optionIndex < 12; optionIndex++)
                {
                    prompt.Append(optionIndex + 1).Append(") ").AppendLine(BoundText(Convert.ToString(options[optionIndex]), 500));
                }
            }
            prompt.AppendLine();
        }

        if (prompt.Length > 24000) throw new InvalidOperationException("This quiz is too large to send in one request. Try a shorter quiz section.");
        return prompt.ToString();
    }

    private static Credentials EnsureFreshCredentials(Credentials credentials)
    {
        if (credentials.ExpiresAt > UnixNow() + 90) return credentials;
        string responseJson = PostForm(TokenEndpoint, new Dictionary<string, string>
        {
            { "grant_type", "refresh_token" },
            { "client_id", credentials.ClientId },
            { "refresh_token", credentials.RefreshToken },
            { "resource", Resource }
        });
        Dictionary<string, object> refreshed = ParseObject(responseJson);
        string accessToken = GetString(refreshed, "access_token");
        string refreshToken = GetString(refreshed, "refresh_token");
        if (String.IsNullOrWhiteSpace(accessToken) || String.IsNullOrWhiteSpace(refreshToken)) throw new InvalidOperationException("ChatGPT could not refresh the connection. Sign in again.");

        credentials.AccessToken = accessToken;
        credentials.RefreshToken = refreshToken;
        credentials.Scope = GetString(refreshed, "scope", credentials.Scope);
        credentials.ExpiresAt = UnixNow() + GetInt(refreshed, "expires_in", 3600);
        SaveCredentials(credentials);
        return credentials;
    }

    private static string GetFirstVisibleModel(string accessToken)
    {
        string json = GetJson("https://api.openai.com/v1/models", accessToken);
        Dictionary<string, object> document = ParseObject(json);
        object[] models = GetArray(document, "models");
        if (models == null) throw new InvalidOperationException("ChatGPT did not return an available model list.");
        foreach (object item in models)
        {
            Dictionary<string, object> model = ToDictionary(item);
            if (String.Equals(GetString(model, "visibility"), "list", StringComparison.OrdinalIgnoreCase))
            {
                string slug = GetString(model, "slug");
                if (!String.IsNullOrWhiteSpace(slug)) return slug;
            }
        }
        throw new InvalidOperationException("No ChatGPT model is currently available to this account.");
    }

    private static string RunResponsesRequest(string accessToken, string model, string prompt)
    {
        string instructions = "You are the Coursera Tools quiz assistant. Answer only the supplied questions. Never invent missing context. Keep explanations concise. Return the exact JSON format requested in the user input.";
        Dictionary<string, object> inputItem = new Dictionary<string, object>
        {
            { "role", "user" },
            { "content", prompt }
        };
        Dictionary<string, object> body = new Dictionary<string, object>
        {
            { "model", model },
            { "instructions", instructions },
            { "input", new object[] { inputItem } },
            { "store", false },
            { "stream", true }
        };

        HttpWebRequest request = (HttpWebRequest)WebRequest.Create("https://api.openai.com/v1/responses");
        request.Method = "POST";
        request.ContentType = "application/json";
        request.Accept = "text/event-stream";
        request.Headers[HttpRequestHeader.Authorization] = "Bearer " + accessToken;
        request.Timeout = 120000;
        request.ReadWriteTimeout = 120000;
        byte[] payload = Encoding.UTF8.GetBytes(Json.Serialize(body));
        lock (StateLock)
        {
            if (_quizCancelled) throw new OperationCanceledException("Quiz request was cancelled.");
            _activeInferenceRequest = request;
        }

        StringBuilder answer = new StringBuilder();
        bool completed = false;
        try
        {
            using (Stream stream = request.GetRequestStream()) stream.Write(payload, 0, payload.Length);
            using (HttpWebResponse response = (HttpWebResponse)request.GetResponse())
            using (StreamReader reader = new StreamReader(response.GetResponseStream(), Encoding.UTF8))
            {
                string line;
                while ((line = reader.ReadLine()) != null)
                {
                    ThrowIfQuizCancelled();
                    if (!line.StartsWith("data:", StringComparison.Ordinal)) continue;
                    string data = line.Substring(5).Trim();
                    if (data == "[DONE]" || data.Length == 0) continue;
                    Dictionary<string, object> item = ParseObject(data);
                    string type = GetString(item, "type");
                    if (type == "response.output_text.delta")
                    {
                        answer.Append(GetString(item, "delta"));
                        if (answer.Length > 30000) throw new InvalidOperationException("ChatGPT returned a response that was too long.");
                    }
                    else if (type == "response.failed")
                    {
                        Dictionary<string, object> responseData = GetObject(item, "response");
                        Dictionary<string, object> error = GetObject(responseData, "error");
                        string code = GetString(error, "code");
                        if (code == "subscription_sharing_usage_limit_exceeded" || code == "subscription_sharing_usage_unavailable")
                            throw new InvalidOperationException("Your ChatGPT plan usage limit was reached or is unavailable. Review usage in ChatGPT settings.");
                        throw new InvalidOperationException("ChatGPT could not answer this quiz request.");
                    }
                    else if (type == "response.completed")
                    {
                        completed = true;
                    }
                    else if (type == "response.incomplete")
                    {
                        throw new InvalidOperationException("ChatGPT returned an incomplete answer. Try again.");
                    }
                }
            }
        }
        catch (WebException ex)
        {
            if (_quizCancelled) throw new OperationCanceledException("Quiz request was cancelled.", ex);
            throw new InvalidOperationException(ReadWebError(ex));
        }
        finally
        {
            lock (StateLock)
            {
                if (Object.ReferenceEquals(_activeInferenceRequest, request)) _activeInferenceRequest = null;
            }
        }

        ThrowIfQuizCancelled();
        if (!completed || answer.Length == 0) throw new InvalidOperationException("ChatGPT did not finish the answer. Try again.");
        return answer.ToString();
    }

    private static void CancelQuizRequest()
    {
        HttpWebRequest request;
        lock (StateLock)
        {
            _quizCancelled = true;
            request = _activeInferenceRequest;
        }
        if (request != null)
        {
            try { request.Abort(); }
            catch { }
        }
    }

    private static void ThrowIfQuizCancelled()
    {
        if (_quizCancelled) throw new OperationCanceledException("Quiz request was cancelled.");
    }

    private static void RevokeRefreshToken(Credentials credentials)
    {
        Dictionary<string, object> metadata = ParseObject(GetJson(Issuer + "/.well-known/openid-configuration", null));
        string endpoint = GetString(metadata, "revocation_endpoint");
        Uri endpointUri;
        if (!Uri.TryCreate(endpoint, UriKind.Absolute, out endpointUri) || endpointUri.Scheme != Uri.UriSchemeHttps || !String.Equals(endpointUri.Host, "auth.openai.com", StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException("OpenAI did not provide a trusted token revocation endpoint.");

        PostForm(endpoint, new Dictionary<string, string>
        {
            { "token", credentials.RefreshToken },
            { "token_type_hint", "refresh_token" },
            { "client_id", credentials.ClientId }
        });
    }

    private static string GetJson(string url, string accessToken)
    {
        HttpWebRequest request = (HttpWebRequest)WebRequest.Create(url);
        request.Method = "GET";
        bool trackForQuiz = !String.IsNullOrWhiteSpace(accessToken);
        if (trackForQuiz)
        {
            request.Headers[HttpRequestHeader.Authorization] = "Bearer " + accessToken;
            lock (StateLock)
            {
                if (_quizCancelled) throw new OperationCanceledException("Quiz request was cancelled.");
                _activeInferenceRequest = request;
            }
        }
        request.Timeout = 30000;
        try
        {
            using (HttpWebResponse response = (HttpWebResponse)request.GetResponse())
            using (StreamReader reader = new StreamReader(response.GetResponseStream(), Encoding.UTF8)) return reader.ReadToEnd();
        }
        catch (WebException ex)
        {
            if (trackForQuiz && _quizCancelled) throw new OperationCanceledException("Quiz request was cancelled.", ex);
            throw;
        }
        finally
        {
            if (trackForQuiz)
            {
                lock (StateLock)
                {
                    if (Object.ReferenceEquals(_activeInferenceRequest, request)) _activeInferenceRequest = null;
                }
            }
        }
    }

    private static string PostForm(string url, Dictionary<string, string> fields)
    {
        StringBuilder form = new StringBuilder();
        foreach (KeyValuePair<string, string> field in fields)
        {
            if (form.Length > 0) form.Append('&');
            form.Append(Url(field.Key)).Append('=').Append(Url(field.Value));
        }
        byte[] payload = Encoding.UTF8.GetBytes(form.ToString());
        HttpWebRequest request = (HttpWebRequest)WebRequest.Create(url);
        request.Method = "POST";
        request.ContentType = "application/x-www-form-urlencoded";
        request.Timeout = 30000;
        request.ReadWriteTimeout = 30000;
        using (Stream stream = request.GetRequestStream()) stream.Write(payload, 0, payload.Length);
        try
        {
            using (HttpWebResponse response = (HttpWebResponse)request.GetResponse())
            using (StreamReader reader = new StreamReader(response.GetResponseStream(), Encoding.UTF8)) return reader.ReadToEnd();
        }
        catch (WebException ex)
        {
            throw new InvalidOperationException(ReadWebError(ex));
        }
    }

    private static Dictionary<string, object> ValidateIdToken(string token, string clientId, string nonce)
    {
        string[] parts = token.Split('.');
        if (parts.Length != 3) throw new InvalidOperationException("ChatGPT returned an invalid identity token.");
        Dictionary<string, object> header = ParseObject(Encoding.UTF8.GetString(FromBase64Url(parts[0])));
        Dictionary<string, object> claims = ParseObject(Encoding.UTF8.GetString(FromBase64Url(parts[1])));
        string algorithm = GetString(header, "alg");
        string keyId = GetString(header, "kid");
        if (algorithm != "RS256" || String.IsNullOrWhiteSpace(keyId)) throw new InvalidOperationException("ChatGPT returned an unsupported identity token.");

        string jwksJson = GetJson(JwksEndpoint, null);
        Dictionary<string, object> jwks = ParseObject(jwksJson);
        object[] keys = GetArray(jwks, "keys");
        Dictionary<string, object> selectedKey = null;
        if (keys != null)
        {
            foreach (object rawKey in keys)
            {
                Dictionary<string, object> key = ToDictionary(rawKey);
                if (String.Equals(GetString(key, "kid"), keyId, StringComparison.Ordinal))
                {
                    selectedKey = key;
                    break;
                }
            }
        }
        if (selectedKey == null || GetString(selectedKey, "kty") != "RSA") throw new InvalidOperationException("ChatGPT signing key could not be verified.");

        RSAParameters parameters = new RSAParameters
        {
            Modulus = FromBase64Url(GetString(selectedKey, "n")),
            Exponent = FromBase64Url(GetString(selectedKey, "e"))
        };
        byte[] signingInput = Encoding.ASCII.GetBytes(parts[0] + "." + parts[1]);
        byte[] signature = FromBase64Url(parts[2]);
        bool signatureValid;
        using (RSACryptoServiceProvider rsa = new RSACryptoServiceProvider())
        using (SHA256CryptoServiceProvider sha256 = new SHA256CryptoServiceProvider())
        {
            rsa.ImportParameters(parameters);
            signatureValid = rsa.VerifyData(signingInput, sha256, signature);
        }
        if (!signatureValid) throw new InvalidOperationException("ChatGPT identity token signature verification failed.");

        long issuedAt = GetLong(claims, "iat");
        long expiresAt = GetLong(claims, "exp");
        long now = UnixNow();
        if (!String.Equals(GetString(claims, "iss"), Issuer, StringComparison.Ordinal)) throw new InvalidOperationException("ChatGPT identity token issuer did not match.");
        if (!AudienceMatches(claims, clientId)) throw new InvalidOperationException("ChatGPT identity token audience did not match.");
        if (issuedAt <= 0 || issuedAt > now + 60 || expiresAt <= issuedAt || expiresAt <= now) throw new InvalidOperationException("ChatGPT identity token timestamps were invalid.");
        if (!FixedTimeEquals(nonce, GetString(claims, "nonce"))) throw new InvalidOperationException("ChatGPT identity token nonce did not match.");
        if (String.IsNullOrWhiteSpace(GetString(claims, "sub"))) throw new InvalidOperationException("ChatGPT identity token did not include an account identifier.");
        return claims;
    }

    private static bool AudienceMatches(Dictionary<string, object> claims, string clientId)
    {
        object audience;
        if (!claims.TryGetValue("aud", out audience)) return false;
        string single = audience as string;
        if (single != null) return String.Equals(single, clientId, StringComparison.Ordinal);
        object[] list = audience as object[];
        if (list == null) return false;
        foreach (object item in list) if (String.Equals(Convert.ToString(item), clientId, StringComparison.Ordinal)) return true;
        return false;
    }

    private static bool HasPlanScope(string scope)
    {
        if (String.IsNullOrWhiteSpace(scope)) return false;
        string[] scopes = scope.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
        bool direct = false;
        bool invoke = false;
        foreach (string item in scopes)
        {
            if (item == "chatgpt.tokens.use.direct") direct = true;
            if (item == "resource.invoke") invoke = true;
        }
        return direct && invoke;
    }

    private static string CredentialPath()
    {
        return Path.Combine(AppDataPath(), CredentialFileName);
    }

    private static string AppDataPath()
    {
        string path = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "CourseraTools");
        Directory.CreateDirectory(path);
        return path;
    }

    private static string LoadOrCreateHostId()
    {
        string path = Path.Combine(AppDataPath(), HostIdFileName);
        if (File.Exists(path))
        {
            string current = File.ReadAllText(path, Encoding.UTF8).Trim();
            if (current.StartsWith("urn:uuid:", StringComparison.Ordinal) && current.Length < 64) return current;
        }
        string hostId = "urn:uuid:" + Guid.NewGuid().ToString("D");
        File.WriteAllText(path, hostId, new UTF8Encoding(false));
        return hostId;
    }

    private static Credentials LoadCredentials()
    {
        string path = CredentialPath();
        if (!File.Exists(path)) return null;
        byte[] encrypted = File.ReadAllBytes(path);
        byte[] entropy = Encoding.UTF8.GetBytes("Coursera Tools ChatGPT credentials v1");
        byte[] plain = ProtectedData.Unprotect(encrypted, entropy, DataProtectionScope.CurrentUser);
        return Json.Deserialize<Credentials>(Encoding.UTF8.GetString(plain));
    }

    private static void SaveCredentials(Credentials credentials)
    {
        string path = CredentialPath();
        string tempPath = path + ".tmp";
        byte[] plain = Encoding.UTF8.GetBytes(Json.Serialize(credentials));
        byte[] entropy = Encoding.UTF8.GetBytes("Coursera Tools ChatGPT credentials v1");
        byte[] encrypted = ProtectedData.Protect(plain, entropy, DataProtectionScope.CurrentUser);
        File.WriteAllBytes(tempPath, encrypted);
        if (File.Exists(path)) File.Replace(tempPath, path, null);
        else File.Move(tempPath, path);
    }

    private static string ReadWebError(WebException exception)
    {
        string body = "";
        try
        {
            if (exception.Response != null)
            {
                using (Stream stream = exception.Response.GetResponseStream())
                using (StreamReader reader = new StreamReader(stream, Encoding.UTF8)) body = reader.ReadToEnd();
            }
        }
        catch { }

        if (body.IndexOf("subscription_sharing_usage_limit_exceeded", StringComparison.OrdinalIgnoreCase) >= 0 || body.IndexOf("subscription_sharing_usage_unavailable", StringComparison.OrdinalIgnoreCase) >= 0)
            return "Your ChatGPT plan usage limit was reached or is unavailable. Review usage in ChatGPT settings.";
        if (body.IndexOf("invalid_grant", StringComparison.OrdinalIgnoreCase) >= 0)
            return "The ChatGPT connection expired. Disconnect, then sign in again.";
        return "OpenAI could not complete the request. Check your ChatGPT plan access and try again.";
    }

    private static string SafeMessage(Exception exception)
    {
        if (exception is WebException) return ReadWebError((WebException)exception);
        string message = exception == null ? "Unexpected error." : exception.Message;
        if (message.Length > 240) message = message.Substring(0, 240);
        return message;
    }

    private static string RandomToken(int byteCount)
    {
        byte[] bytes = new byte[byteCount];
        using (RandomNumberGenerator random = RandomNumberGenerator.Create()) random.GetBytes(bytes);
        return Base64Url(bytes);
    }

    private static string Base64Url(byte[] value)
    {
        return Convert.ToBase64String(value).TrimEnd('=').Replace('+', '-').Replace('/', '_');
    }

    private static byte[] FromBase64Url(string value)
    {
        string normalized = value.Replace('-', '+').Replace('_', '/');
        switch (normalized.Length % 4)
        {
            case 2: normalized += "=="; break;
            case 3: normalized += "="; break;
        }
        return Convert.FromBase64String(normalized);
    }

    private static string Url(string value)
    {
        return Uri.EscapeDataString(value ?? "");
    }

    private static long UnixNow()
    {
        return (long)(DateTime.UtcNow - new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc)).TotalSeconds;
    }

    private static bool FixedTimeEquals(string expected, string actual)
    {
        if (expected == null || actual == null || expected.Length != actual.Length) return false;
        int difference = 0;
        for (int i = 0; i < expected.Length; i++) difference |= expected[i] ^ actual[i];
        return difference == 0;
    }

    private static string BoundText(string value, int maximum)
    {
        if (value == null) return "";
        value = value.Trim();
        return value.Length <= maximum ? value : value.Substring(0, maximum);
    }

    private static Dictionary<string, string> ParseQuery(string query)
    {
        Dictionary<string, string> result = new Dictionary<string, string>(StringComparer.Ordinal);
        if (String.IsNullOrWhiteSpace(query)) return result;
        foreach (string pair in query.TrimStart('?').Split('&'))
        {
            if (pair.Length == 0) continue;
            string[] parts = pair.Split(new[] { '=' }, 2);
            string key = Uri.UnescapeDataString(parts[0].Replace('+', ' '));
            string value = parts.Length > 1 ? Uri.UnescapeDataString(parts[1].Replace('+', ' ')) : "";
            if (!result.ContainsKey(key)) result.Add(key, value);
        }
        return result;
    }

    private static void WriteHttpResponse(NetworkStream stream, int statusCode, string message)
    {
        string escaped = System.Security.SecurityElement.Escape(message ?? "");
        string html = "<!doctype html><html><head><meta charset=\"utf-8\"><title>Coursera Tools</title></head><body style=\"font:16px Segoe UI,sans-serif;max-width:620px;margin:12vh auto;padding:24px;color:#202b38\"><h1>Coursera Tools</h1><p>" + escaped + "</p></body></html>";
        byte[] body = Encoding.UTF8.GetBytes(html);
        string reason = statusCode == 200 ? "OK" : (statusCode == 404 ? "Not Found" : (statusCode == 405 ? "Method Not Allowed" : "Bad Request"));
        byte[] headers = Encoding.ASCII.GetBytes("HTTP/1.1 " + statusCode + " " + reason + "\r\nContent-Type: text/html; charset=utf-8\r\nCache-Control: no-store\r\nConnection: close\r\nContent-Length: " + body.Length + "\r\n\r\n");
        stream.Write(headers, 0, headers.Length);
        stream.Write(body, 0, body.Length);
        stream.Flush();
    }

    private static object ReadNativeMessage(Stream input)
    {
        int first = input.ReadByte();
        if (first < 0) return null;
        byte[] lengthBytes = new byte[4];
        lengthBytes[0] = (byte)first;
        ReadExactly(input, lengthBytes, 1, 3);
        int length = BitConverter.ToInt32(lengthBytes, 0);
        if (length <= 0 || length > 1024 * 1024) throw new InvalidDataException("Message size is outside the allowed range.");
        byte[] payload = new byte[length];
        ReadExactly(input, payload, 0, length);
        return Json.DeserializeObject(Encoding.UTF8.GetString(payload));
    }

    private static void ReadExactly(Stream stream, byte[] buffer, int offset, int length)
    {
        int read = 0;
        while (read < length)
        {
            int count = stream.Read(buffer, offset + read, length - read);
            if (count <= 0) throw new EndOfStreamException("Native messaging input ended unexpectedly.");
            read += count;
        }
    }

    private static void WriteMessage(object message)
    {
        byte[] payload = Encoding.UTF8.GetBytes(Json.Serialize(message));
        if (payload.Length > 1024 * 1024) return;
        byte[] length = BitConverter.GetBytes(payload.Length);
        lock (OutputLock)
        {
            Stream output = Console.OpenStandardOutput();
            output.Write(length, 0, length.Length);
            output.Write(payload, 0, payload.Length);
            output.Flush();
        }
    }

    private static void WriteError(string requestId, string message)
    {
        WriteMessage(new Dictionary<string, object>
        {
            { "requestId", requestId ?? "" },
            { "type", "error" },
            { "error", message ?? "Unexpected error." }
        });
    }

    private static Dictionary<string, object> ParseObject(string json)
    {
        return ToDictionary(Json.DeserializeObject(json));
    }

    private static Dictionary<string, object> ToDictionary(object value)
    {
        Dictionary<string, object> result = value as Dictionary<string, object>;
        if (result == null) throw new InvalidDataException("Expected a JSON object.");
        return result;
    }

    private static Dictionary<string, object> GetObject(Dictionary<string, object> source, string key)
    {
        object value;
        if (source != null && source.TryGetValue(key, out value) && value is Dictionary<string, object>) return (Dictionary<string, object>)value;
        return new Dictionary<string, object>();
    }

    private static object[] GetArray(Dictionary<string, object> source, string key)
    {
        object value;
        if (source != null && source.TryGetValue(key, out value)) return value as object[];
        return null;
    }

    private static string GetString(Dictionary<string, object> source, string key, string fallback)
    {
        object value;
        if (source != null && source.TryGetValue(key, out value) && value != null) return Convert.ToString(value);
        return fallback;
    }

    private static string GetString(Dictionary<string, object> source, string key)
    {
        return GetString(source, key, "");
    }

    private static string GetString(Dictionary<string, string> source, string key)
    {
        string value;
        return source != null && source.TryGetValue(key, out value) ? value : "";
    }

    private static int GetInt(Dictionary<string, object> source, string key, int fallback)
    {
        object value;
        int result;
        return source != null && source.TryGetValue(key, out value) && Int32.TryParse(Convert.ToString(value), out result) ? result : fallback;
    }

    private static long GetLong(Dictionary<string, object> source, string key)
    {
        object value;
        long result;
        return source != null && source.TryGetValue(key, out value) && Int64.TryParse(Convert.ToString(value), out result) ? result : 0;
    }
}
