import { useState, useEffect } from "react";
import { Link, Route, Routes } from "react-router-dom";
import { Brain, FileText, MessageSquare, Upload } from "lucide-react";
import toast, { Toaster } from "react-hot-toast";
import { askQuestion, uploadPDF, getDocuments, getChatHistory } from "./api/api";
import {
  SignedIn,
  SignedOut,
  SignInButton,
  SignUpButton,
  UserButton,
  RedirectToSignIn,
} from "@clerk/clerk-react";
function Home() {
  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />

      <section className="px-8 py-20 text-center">
        <h2 className="text-5xl font-bold text-slate-900">
          Chat with your PDFs using AI
        </h2>

        <p className="max-w-2xl mx-auto mt-5 text-lg text-slate-600">
          Upload notes, PDFs, and study material. Ask questions and get answers
          only from your uploaded documents using RAG, embeddings, ChromaDB, and
          Gemini AI.
        </p>

        <div className="flex justify-center gap-4 mt-8">
          <Link
            to="/upload"
            className="px-6 py-3 text-white bg-indigo-600 rounded-xl hover:bg-indigo-700"
          >
            Upload PDF
          </Link>

          <Link
            to="/chat"
            className="px-6 py-3 bg-white border rounded-xl hover:bg-slate-100"
          >
            Start Chat
          </Link>
        </div>
      </section>

      <section className="grid max-w-5xl grid-cols-1 gap-6 px-8 mx-auto md:grid-cols-3">
        <FeatureCard
          icon={<Upload />}
          title="Upload PDFs"
          description="Upload your notes, books, research papers, and documents."
        />
        <FeatureCard
          icon={<FileText />}
          title="Extract Knowledge"
          description="Extract text, split it into chunks, and create embeddings."
        />
        <FeatureCard
          icon={<MessageSquare />}
          title="Chat with Docs"
          description="Ask questions and get AI answers from your document content."
        />
      </section>
    </div>
  );
}

function Dashboard() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);

  const selectedFile = localStorage.getItem("selectedFile");

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const data = await getDocuments();
      setDocuments(data.documents || []);
    } catch (error) {
      console.error(error);
      toast.error("Failed to load documents");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  const handleSelectDocument = (filename) => {
    localStorage.setItem("selectedFile", filename);
    toast.success(`${filename} selected for chat`);
  };

  return (
    <PageLayout title="Dashboard">
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <StatCard title="Documents" value={documents.length} />
        <StatCard title="RAG Status" value="Active" />
        <StatCard title="AI Model" value="Gemini" />
      </div>

      {selectedFile && (
        <div className="p-4 mt-8 bg-indigo-50 border border-indigo-200 rounded-xl">
          <strong>Current selected document:</strong> {selectedFile}
        </div>
      )}

      <div className="p-6 mt-8 bg-white border shadow-sm rounded-2xl">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-xl font-semibold">Uploaded Documents</h3>

          <button
            onClick={loadDocuments}
            className="px-4 py-2 border rounded-xl hover:bg-slate-100"
          >
            Refresh
          </button>
        </div>

        {loading && <p className="text-slate-500">Loading documents...</p>}

        {!loading && documents.length === 0 && (
          <p className="text-slate-500">
            No documents uploaded yet. Upload your first PDF.
          </p>
        )}

        {!loading && documents.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-left border">
              <thead className="bg-slate-100">
                <tr>
                  <th className="p-3 border">Filename</th>
                  <th className="p-3 border">Characters</th>
                  <th className="p-3 border">Chunks</th>
                  <th className="p-3 border">Uploaded At</th>
                  <th className="p-3 border">Action</th>
                </tr>
              </thead>

              <tbody>
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50">
                    <td className="p-3 border">{doc.filename}</td>
                    <td className="p-3 border">{doc.characters_extracted}</td>
                    <td className="p-3 border">{doc.chunks_stored}</td>
                    <td className="p-3 border">
                      {new Date(doc.created_at).toLocaleString()}
                    </td>
                    <td className="p-3 border">
                      <button
                        onClick={() => handleSelectDocument(doc.filename)}
                        className="px-4 py-2 text-white bg-indigo-600 rounded-xl hover:bg-indigo-700"
                      >
                        Select
                      </button>

                      <Link
                        to="/chat"
                        onClick={() => handleSelectDocument(doc.filename)}
                        className="inline-block px-4 py-2 ml-2 border rounded-xl hover:bg-slate-100"
                      >
                        Chat
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </PageLayout>
  );
}

function UploadPage() {
  const [file, setFile] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!file) {
      toast.error("Please choose a PDF file first");
      return;
    }

    if (file.type !== "application/pdf") {
      toast.error("Only PDF files are allowed");
      return;
    }

    try {
      setLoading(true);
      setUploadResult(null);

      const data = await uploadPDF(file);

      setUploadResult(data);
      localStorage.setItem("selectedFile", data.filename);
      toast.success("PDF uploaded successfully");
    } catch (error) {
      console.error(error);
      toast.error("PDF upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageLayout title="Upload PDF">
      <div className="max-w-2xl p-8 bg-white border shadow-sm rounded-2xl">
        <label className="block mb-3 font-medium">Choose PDF file</label>

        <input
          type="file"
          accept="application/pdf"
          onChange={(e) => setFile(e.target.files[0])}
          className="w-full p-3 border rounded-xl"
        />

        {file && (
          <p className="mt-3 text-sm text-slate-600">
            Selected file: <strong>{file.name}</strong>
          </p>
        )}

        <button
          onClick={handleUpload}
          disabled={loading}
          className="w-full px-5 py-3 mt-5 text-white bg-indigo-600 rounded-xl hover:bg-indigo-700 disabled:bg-slate-400"
        >
          {loading ? "Uploading and processing..." : "Upload Document"}
        </button>
      </div>

      {uploadResult && (
        <div className="max-w-2xl p-6 mt-6 bg-white border shadow-sm rounded-2xl">
          <h3 className="mb-4 text-xl font-semibold text-green-700">
            Upload Successful
          </h3>

          <p>
            <strong>Filename:</strong> {uploadResult.filename}
          </p>
          <p>
            <strong>Characters extracted:</strong>{" "}
            {uploadResult.characters_extracted}
          </p>
          <p>
            <strong>Chunks stored:</strong> {uploadResult.chunks_stored}
          </p>

          <div className="p-4 mt-4 rounded-xl bg-slate-100">
            <strong>Preview:</strong>
            <p className="mt-2 text-sm text-slate-700 whitespace-pre-wrap">
              {uploadResult.preview}
            </p>
          </div>

          <Link
            to="/chat"
            className="inline-block px-5 py-3 mt-5 text-white bg-indigo-600 rounded-xl hover:bg-indigo-700"
          >
            Chat with PDF
          </Link>
        </div>
      )}
    </PageLayout>
  );
}

function ChatPage() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);

  const selectedFile = localStorage.getItem("selectedFile");

  const loadChatHistory = async () => {
    if (!selectedFile) {
      toast.error("Please select or upload a PDF first");
      return;
    }

    try {
      setHistoryLoading(true);

      const data = await getChatHistory(selectedFile);

      setHistory(data.history || []);
    } catch (error) {
      console.error(error);
      toast.error("Failed to load chat history");
    } finally {
      setHistoryLoading(false);
    }
  };

  const handleAsk = async () => {
    if (!question.trim()) {
      toast.error("Please enter a question");
      return;
    }

    if (!selectedFile) {
      toast.error("Please upload a PDF first");
      return;
    }

    const userQuestion = question;
    setQuestion("");

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        text: userQuestion,
      },
    ]);

    try {
      setLoading(true);

      const data = await askQuestion(userQuestion, selectedFile);

      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          text: data.answer,
          sources: data.sources,
        },
      ]);

      await loadChatHistory();
    } catch (error) {
      console.error(error);
      toast.error("Failed to get answer");

      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          text: "Something went wrong while getting the AI answer.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageLayout title="Chat with PDF">
      {selectedFile ? (
        <div className="max-w-4xl p-4 mb-4 bg-indigo-50 border border-indigo-200 rounded-xl">
          <strong>Selected document:</strong> {selectedFile}
        </div>
      ) : (
        <div className="max-w-4xl p-4 mb-4 bg-yellow-50 border border-yellow-200 rounded-xl">
          No PDF selected. Please upload a PDF first.
        </div>
      )}

      <div className="grid max-w-6xl grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 bg-white border shadow-sm rounded-2xl">
          <div className="h-[500px] p-5 overflow-y-auto border-b">
            {messages.length === 0 && (
              <p className="text-slate-500">
                Upload a PDF first, then ask questions from your selected
                document.
              </p>
            )}

            <div className="space-y-4">
              {messages.map((msg, index) => (
                <div
                  key={index}
                  className={`p-4 rounded-2xl ${
                    msg.role === "user"
                      ? "ml-auto bg-indigo-600 text-white max-w-xl"
                      : "mr-auto bg-slate-100 text-slate-900 max-w-2xl"
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.text}</p>

                  {msg.sources && msg.sources.length > 0 && (
                    <div className="pt-3 mt-3 text-sm border-t border-slate-300">
                      <strong>Source:</strong> {msg.sources.join(", ")}
                    </div>
                  )}
                </div>
              ))}

              {loading && (
                <div className="max-w-xl p-4 rounded-2xl bg-slate-100">
                  AI is thinking...
                </div>
              )}
            </div>
          </div>

          <div className="flex gap-3 p-4">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  handleAsk();
                }
              }}
              placeholder="Ask a question from your PDF..."
              className="flex-1 px-4 py-3 border rounded-xl"
            />

            <button
              onClick={handleAsk}
              disabled={loading}
              className="px-6 py-3 text-white bg-indigo-600 rounded-xl hover:bg-indigo-700 disabled:bg-slate-400"
            >
              Ask
            </button>
          </div>
        </div>

        <div className="p-5 bg-white border shadow-sm rounded-2xl">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Chat History</h3>

            <button
              onClick={loadChatHistory}
              disabled={historyLoading || !selectedFile}
              className="px-3 py-2 text-sm border rounded-xl hover:bg-slate-100 disabled:bg-slate-100 disabled:text-slate-400"
            >
              {historyLoading ? "Loading..." : "Refresh"}
            </button>
          </div>

          {!selectedFile && (
            <p className="text-sm text-slate-500">
              Select a document to view chat history.
            </p>
          )}

          {selectedFile && history.length === 0 && !historyLoading && (
            <p className="text-sm text-slate-500">
              No chat history yet for this document.
            </p>
          )}

          <div className="space-y-4 max-h-[520px] overflow-y-auto">
            {history.map((item) => (
              <div key={item.id} className="p-4 border rounded-xl bg-slate-50">
                <p className="mb-2 text-sm font-semibold text-indigo-700">
                  Q: {item.question}
                </p>

                <p className="text-sm text-slate-700 whitespace-pre-wrap">
                  {item.answer}
                </p>

                <p className="mt-3 text-xs text-slate-500">
                  {new Date(item.created_at).toLocaleString()}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </PageLayout>
  );
}

function Navbar() {
  return (
    <nav className="flex items-center justify-between px-8 py-5 bg-white border-b">
      <Link to="/" className="flex items-center gap-2">
        <Brain className="text-indigo-600" />
        <h1 className="text-xl font-bold">AI Knowledge Workspace</h1>
      </Link>

      <div className="flex items-center gap-4">
        <SignedIn>
          <Link
            to="/dashboard"
            className="text-slate-700 hover:text-indigo-600"
          >
            Dashboard
          </Link>
          <Link to="/upload" className="text-slate-700 hover:text-indigo-600">
            Upload
          </Link>
          <Link to="/chat" className="text-slate-700 hover:text-indigo-600">
            Chat
          </Link>
          <UserButton afterSignOutUrl="/" />
        </SignedIn>

        <SignedOut>
          <SignInButton mode="modal">
            <button className="px-4 py-2 border rounded-xl hover:bg-slate-100">
              Login
            </button>
          </SignInButton>

          <SignUpButton mode="modal">
            <button className="px-4 py-2 text-white bg-indigo-600 rounded-xl hover:bg-indigo-700">
              Sign Up
            </button>
          </SignUpButton>
        </SignedOut>
      </div>
    </nav>
  );
}

function PageLayout({ title, children }) {
  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />

      <main className="px-8 py-10">
        <h2 className="mb-8 text-3xl font-bold">{title}</h2>
        {children}
      </main>
    </div>
  );
}

function FeatureCard({ icon, title, description }) {
  return (
    <div className="p-6 bg-white border shadow-sm rounded-2xl">
      <div className="mb-4 text-indigo-600">{icon}</div>
      <h3 className="mb-2 text-xl font-semibold">{title}</h3>
      <p className="text-slate-600">{description}</p>
    </div>
  );
}

function StatCard({ title, value }) {
  return (
    <div className="p-6 bg-white border shadow-sm rounded-2xl">
      <p className="text-slate-500">{title}</p>
      <h3 className="mt-2 text-3xl font-bold">{value}</h3>
    </div>
  );
}

function ProtectedRoute({ children }) {
  return (
    <>
      <SignedIn>{children}</SignedIn>
      <SignedOut>
        <div className="flex items-center justify-center min-h-screen bg-slate-50">
          <div className="max-w-md p-8 text-center bg-white border shadow-sm rounded-2xl">
            <Brain className="mx-auto mb-4 text-indigo-600" size={42} />
            <h2 className="mb-3 text-2xl font-bold">Login Required</h2>
            <p className="mb-6 text-slate-600">
              Please login to access your AI Knowledge Workspace.
            </p>

            <SignInButton mode="modal">
              <button className="w-full px-5 py-3 text-white bg-indigo-600 rounded-xl hover:bg-indigo-700">
                Login
              </button>
            </SignInButton>

            <SignUpButton mode="modal">
              <button className="w-full px-5 py-3 mt-3 border rounded-xl hover:bg-slate-100">
                Create Account
              </button>
            </SignUpButton>
          </div>
        </div>
      </SignedOut>
    </>
  );
}
export default function App() {
  return (
    <>
      <Toaster position="top-right" />

      <Routes>
        <Route path="/" element={<Home />} />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/upload"
          element={
            <ProtectedRoute>
              <UploadPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/chat"
          element={
            <ProtectedRoute>
              <ChatPage />
            </ProtectedRoute>
          }
        />
      </Routes>
    </>
  );
}
