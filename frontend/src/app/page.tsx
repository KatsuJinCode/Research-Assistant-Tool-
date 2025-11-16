export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">Research Assistant Tool</h1>
        <p className="text-xl text-gray-600 mb-8">
          AI-powered research assistant for gathering and analyzing information
        </p>
        <div className="text-sm text-gray-500">
          <p>Frontend: Next.js + TypeScript</p>
          <p>Backend: FastAPI + Python</p>
          <p className="mt-4">🚧 Currently in development 🚧</p>
        </div>
      </div>
    </main>
  );
}
