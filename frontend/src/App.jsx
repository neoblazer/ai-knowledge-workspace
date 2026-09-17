import { useCallback, useEffect, useState } from "react";
import { Link, Route, Routes } from "react-router-dom";
import { Brain, FileText, MessageSquare, Trash2, Upload } from "lucide-react";
import toast, { Toaster } from "react-hot-toast";
import {
  askQuestion,
  deleteDocument as deleteDocumentRequest,
  getChatHistory,
  getDocuments,
  uploadPDF,
} from "./api/api";
import {
  SignedIn,
  SignedOut,
  SignInButton,
  SignUpButton,
  UserButton,
  useAuth,
} from "@clerk/clerk-react";

function apiErrorMessage(error, fallback) {
  return error?.response?.data?.detail || fallback;
}

function Home() {
  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <section className="px-8 py-20 text-center">
        <h2 className="text-5xl font-bold text-slate-900">Chat with your PDFs using AI</h2>
        <p className="max-w-2xl mx-auto mt-5 text-lg text-slate-600">
          Upload notes, PDFs, and study material. Ask questions and get answers
          only from your uploaded documents using RAG, embeddings, ChromaDB, and Gemini AI.
        </p>
        <div className="flex justify-center gap-4 mt-8">
          <Link to="/upload" className="px-6 py-3 text-white bg-indigo-600 rounded-xl hover:bg-indigo-700">Upload PDF</Link>
          <Link to="/chat" className="px-6 py-3 bg-white border rounded-xl hover:bg-slate-100">Start Chat</Link>
        </div>
      </section>
      <section className="grid max-w-5xl grid-cols-1 gap-6 px-8 mx-auto md:grid-cols-3">
        <FeatureCard icon={<Upload />} title="Upload PDFs" description="Upload your notes, books, research papers, and documents." />
        <FeatureCard icon={<FileText />} title="Extract Knowledge" description="Extract page-aware text chunks and create embeddings." />
        <FeatureCard icon={<MessageSquare />} title="Chat with Docs" description="Ask questions and get grounded answers with page citations." />
      </section>
    </div>
  );
}

function Dashboard() {
  const { getToken } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [selectedDocument, setSelectedDocument] = useState(() => ({
    documentId: localStorage.getItem("selectedDocumentId"),
    filename: localStorage.getItem("selectedFilename"),
  }));

  const loadDocuments = useCallback(async () => {
    try {
      setLoading(true);
      const token = await getToken();
      const data = await getDocuments(token);
      setDocuments(data.documents || []);
    } catch (error) {
      console.error(error);
      toast.error(apiErrorMessage(error, "Failed to load documents"));
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    const timer = window.setTimeout(() => void loadDocuments(), 0);
    return () => window.clearTimeout(timer);
  }, [loadDocuments]);

  const handleSelectDocument = (document) => {
    localStorage.setItem("selectedDocumentId", document.document_id);
    localStorage.setItem("selectedFilename", document.filename);
    localStorage.removeItem("selectedFile");
    setSelectedDocument({ documentId: document.document_id, filename: document.filename });
    toast.success(`${document.filename} selected for chat`);
  };

  const handleDeleteDocument = async (document) => {
    const confirmed = window.confirm(
      `Delete ${document.filename}? This also removes its vectors and chat history.`,
    );
    if (!confirmed) return;
    try {
      setDeletingId(document.document_id);
      const token = await getToken();
      await deleteDocumentRequest(document.document_id, token);
      if (selectedDocument.documentId === document.document_id) {
        localStorage.removeItem("selectedDocumentId");
        localStorage.removeItem("selectedFilename");
        setSelectedDocument({ documentId: null, filename: null });
      }
      toast.success("Document deleted");
      await loadDocuments();
    } catch (error) {
      console.error(error);
      toast.error(apiErrorMessage(error, "Failed to delete document"));
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <PageLayout title="Dashboard">
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <StatCard title="Documents" value={documents.length} />
        <StatCard title="RAG Status" value="Active" />
        <StatCard title="AI Model" value="Gemini" />
      </div>
      {selectedDocument.documentId && (
        <div className="p-4 mt-8 bg-indigo-50 border border-indigo-200 rounded-xl">
          <strong>Current selected document:</strong> {selectedDocument.filename}
        </div>
      )}
      <div className="p-6 mt-8 bg-white border shadow-sm rounded-2xl">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-xl font-semibold">Uploaded Documents</h3>
          <button onClick={loadDocuments} className="px-4 py-2 border rounded-xl hover:bg-slate-100">Refresh</button>
        </div>
        {loading && <p className="text-slate-500">Loading documents...</p>}
        {!loading && documents.length === 0 && <p className="text-slate-500">No documents uploaded yet. Upload your first PDF.</p>}
        {!loading && documents.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-left border">
              <thead className="bg-slate-100"><tr>
                <th className="p-3 border">Filename</th><th className="p-3 border">Characters</th>
                <th className="p-3 border">Chunks</th><th className="p-3 border">Uploaded At</th>
                <th className="p-3 border">Actions</th>
              </tr></thead>
              <tbody>{documents.map((document) => (
                <tr key={document.document_id} className="hover:bg-slate-50">
                  <td className="p-3 border">{document.filename}</td>
                  <td className="p-3 border">{document.characters_extracted}</td>
                  <td className="p-3 border">{document.chunks_stored}</td>
                  <td className="p-3 border">{new Date(document.created_at).toLocaleString()}</td>
                  <td className="p-3 border whitespace-nowrap">
                    <button onClick={() => handleSelectDocument(document)} className="px-3 py-2 text-white bg-indigo-600 rounded-xl hover:bg-indigo-700">Select</button>
                    <Link to="/chat" onClick={() => handleSelectDocument(document)} className="inline-block px-3 py-2 ml-2 border rounded-xl hover:bg-slate-100">Chat</Link>
                    <button
                      onClick={() => handleDeleteDocument(document)}
                      disabled={deletingId === document.document_id}
                      className="inline-flex items-center gap-1 px-3 py-2 ml-2 text-red-700 border border-red-200 rounded-xl hover:bg-red-50 disabled:opacity-50"
                    >
                      <Trash2 size={16} />
                      {deletingId === document.document_id ? "Deleting..." : "Delete"}
                    </button>
                  </td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        )}
      </div>
    </PageLayout>
  );
}

function UploadPage() {
  const { getToken } = useAuth();
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
      const token = await getToken();
      const data = await uploadPDF(file, token);
      setUploadResult(data);
      localStorage.setItem("selectedDocumentId", data.document_id);
      localStorage.setItem("selectedFilename", data.filename);
      localStorage.removeItem("selectedFile");
      toast.success("PDF uploaded successfully");
    } catch (error) {
      console.error(error);
      toast.error(apiErrorMessage(error, "PDF upload failed"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageLayout title="Upload PDF">
      <div className="max-w-2xl p-8 bg-white border shadow-sm rounded-2xl">
        <label className="block mb-3 font-medium">Choose PDF file</label>
        <input type="file" accept="application/pdf" onChange={(event) => setFile(event.target.files[0])} className="w-full p-3 border rounded-xl" />
        {file && <p className="mt-3 text-sm text-slate-600">Selected file: <strong>{file.name}</strong></p>}
        <button onClick={handleUpload} disabled={loading} className="w-full px-5 py-3 mt-5 text-white bg-indigo-600 rounded-xl hover:bg-indigo-700 disabled:bg-slate-400">
          {loading ? "Uploading and processing..." : "Upload Document"}
        </button>
      </div>
      {uploadResult && (
        <div className="max-w-2xl p-6 mt-6 bg-white border shadow-sm rounded-2xl">
          <h3 className="mb-4 text-xl font-semibold text-green-700">Upload Successful</h3>
          <p><strong>Filename:</strong> {uploadResult.filename}</p>
          <p><strong>Characters extracted:</strong> {uploadResult.characters_extracted}</p>
          <p><strong>Chunks stored:</strong> {uploadResult.chunks_stored}</p>
          <div className="p-4 mt-4 rounded-xl bg-slate-100">
            <strong>Preview:</strong>
            <p className="mt-2 text-sm text-slate-700 whitespace-pre-wrap">{uploadResult.preview}</p>
          </div>
          <Link to="/chat" className="inline-block px-5 py-3 mt-5 text-white bg-indigo-600 rounded-xl hover:bg-indigo-700">Chat with PDF</Link>
        </div>
      )}
    </PageLayout>
  );
}

function CitationList({ citations = [] }) {
  if (!citations.length) return null;
  return (
    <div className="pt-3 mt-3 text-sm border-t border-slate-300">
      <strong>Sources:</strong>{" "}
      {citations.map((citation, index) => (
        <span key={`${citation.document_id}-${citation.chunk_index}`}>
          {citation.filename}{citation.page ? ` — Page ${citation.page}` : ""}
          {index < citations.length - 1 ? ", " : ""}
        </span>
      ))}
    </div>
  );
}

function ChatPage() {
  const { getToken } = useAuth();
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const selectedDocumentId = localStorage.getItem("selectedDocumentId");
  const selectedFilename = localStorage.getItem("selectedFilename");

  const loadChatHistory = useCallback(async () => {
    if (!selectedDocumentId) return;
    try {
      setHistoryLoading(true);
      const token = await getToken();
      const data = await getChatHistory(selectedDocumentId, token);
      setHistory(data.history || []);
    } catch (error) {
      console.error(error);
      toast.error(apiErrorMessage(error, "Failed to load chat history"));
    } finally {
      setHistoryLoading(false);
    }
  }, [getToken, selectedDocumentId]);

  useEffect(() => {
    const timer = window.setTimeout(() => void loadChatHistory(), 0);
    return () => window.clearTimeout(timer);
  }, [loadChatHistory]);

  const handleAsk = async () => {
    if (!question.trim()) {
      toast.error("Please enter a question");
      return;
    }
    if (!selectedDocumentId) {
      toast.error("Please select or upload a PDF first");
      return;
    }
    const userQuestion = question.trim();
    setQuestion("");
    setMessages((previous) => [...previous, { role: "user", text: userQuestion }]);
    try {
      setLoading(true);
      const token = await getToken();
      const data = await askQuestion(userQuestion, selectedDocumentId, token);
      setMessages((previous) => [...previous, { role: "ai", text: data.answer, citations: data.citations }]);
      await loadChatHistory();
    } catch (error) {
      console.error(error);
      const message = apiErrorMessage(error, "Unable to generate an answer right now. Please try again.");
      toast.error(message);
      setMessages((previous) => [...previous, { role: "ai", text: message }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageLayout title="Chat with PDF">
      {selectedDocumentId ? (
        <div className="max-w-4xl p-4 mb-4 bg-indigo-50 border border-indigo-200 rounded-xl"><strong>Selected document:</strong> {selectedFilename}</div>
      ) : (
        <div className="max-w-4xl p-4 mb-4 bg-yellow-50 border border-yellow-200 rounded-xl">No PDF selected. Please select a document from the dashboard or upload one.</div>
      )}
      <div className="grid max-w-6xl grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 bg-white border shadow-sm rounded-2xl">
          <div className="h-[500px] p-5 overflow-y-auto border-b">
            {messages.length === 0 && <p className="text-slate-500">Select a PDF, then ask questions from that document.</p>}
            <div className="space-y-4">
              {messages.map((message, index) => (
                <div key={index} className={`p-4 rounded-2xl ${message.role === "user" ? "ml-auto bg-indigo-600 text-white max-w-xl" : "mr-auto bg-slate-100 text-slate-900 max-w-2xl"}`}>
                  <p className="whitespace-pre-wrap">{message.text}</p>
                  <CitationList citations={message.citations} />
                </div>
              ))}
              {loading && <div className="max-w-xl p-4 rounded-2xl bg-slate-100">AI is thinking...</div>}
            </div>
          </div>
          <div className="flex gap-3 p-4">
            <input
              type="text" value={question} onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={(event) => { if (event.key === "Enter") void handleAsk(); }}
              placeholder="Ask a question from your PDF..." className="flex-1 px-4 py-3 border rounded-xl"
            />
            <button onClick={handleAsk} disabled={loading || !selectedDocumentId} className="px-6 py-3 text-white bg-indigo-600 rounded-xl hover:bg-indigo-700 disabled:bg-slate-400">Ask</button>
          </div>
        </div>
        <div className="p-5 bg-white border shadow-sm rounded-2xl">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Chat History</h3>
            <button onClick={loadChatHistory} disabled={historyLoading || !selectedDocumentId} className="px-3 py-2 text-sm border rounded-xl hover:bg-slate-100 disabled:bg-slate-100 disabled:text-slate-400">
              {historyLoading ? "Loading..." : "Refresh"}
            </button>
          </div>
          {!selectedDocumentId && <p className="text-sm text-slate-500">Select a document to view chat history.</p>}
          {selectedDocumentId && history.length === 0 && !historyLoading && <p className="text-sm text-slate-500">No chat history yet for this document.</p>}
          <div className="space-y-4 max-h-[520px] overflow-y-auto">
            {history.map((item) => (
              <div key={item.id} className="p-4 border rounded-xl bg-slate-50">
                <p className="mb-2 text-sm font-semibold text-indigo-700">Q: {item.question}</p>
                <p className="text-sm text-slate-700 whitespace-pre-wrap">{item.answer}</p>
                <CitationList citations={item.citations} />
                <p className="mt-3 text-xs text-slate-500">{new Date(item.created_at).toLocaleString()}</p>
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
      <Link to="/" className="flex items-center gap-2"><Brain className="text-indigo-600" /><h1 className="text-xl font-bold">AI Knowledge Workspace</h1></Link>
      <div className="flex items-center gap-4">
        <SignedIn>
          <Link to="/dashboard" className="text-slate-700 hover:text-indigo-600">Dashboard</Link>
          <Link to="/upload" className="text-slate-700 hover:text-indigo-600">Upload</Link>
          <Link to="/chat" className="text-slate-700 hover:text-indigo-600">Chat</Link>
          <UserButton afterSignOutUrl="/" />
        </SignedIn>
        <SignedOut>
          <SignInButton mode="modal"><button className="px-4 py-2 border rounded-xl hover:bg-slate-100">Login</button></SignInButton>
          <SignUpButton mode="modal"><button className="px-4 py-2 text-white bg-indigo-600 rounded-xl hover:bg-indigo-700">Sign Up</button></SignUpButton>
        </SignedOut>
      </div>
    </nav>
  );
}

function PageLayout({ title, children }) {
  return <div className="min-h-screen bg-slate-50"><Navbar /><main className="px-8 py-10"><h2 className="mb-8 text-3xl font-bold">{title}</h2>{children}</main></div>;
}

function FeatureCard({ icon, title, description }) {
  return <div className="p-6 bg-white border shadow-sm rounded-2xl"><div className="mb-4 text-indigo-600">{icon}</div><h3 className="mb-2 text-xl font-semibold">{title}</h3><p className="text-slate-600">{description}</p></div>;
}

function StatCard({ title, value }) {
  return <div className="p-6 bg-white border shadow-sm rounded-2xl"><p className="text-slate-500">{title}</p><h3 className="mt-2 text-3xl font-bold">{value}</h3></div>;
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
            <p className="mb-6 text-slate-600">Please login to access your AI Knowledge Workspace.</p>
            <SignInButton mode="modal"><button className="w-full px-5 py-3 text-white bg-indigo-600 rounded-xl hover:bg-indigo-700">Login</button></SignInButton>
            <SignUpButton mode="modal"><button className="w-full px-5 py-3 mt-3 border rounded-xl hover:bg-slate-100">Create Account</button></SignUpButton>
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
        <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/upload" element={<ProtectedRoute><UploadPage /></ProtectedRoute>} />
        <Route path="/chat" element={<ProtectedRoute><ChatPage /></ProtectedRoute>} />
      </Routes>
    </>
  );
}
