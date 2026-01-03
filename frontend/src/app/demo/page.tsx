import ChatInterface from "@/components/ChatInterface";

export default function DemoPage() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-8">
      <div className="container mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Chat Demo
          </h1>
          <p className="text-gray-600">
            Try out the AI support assistant with sample course content
          </p>
        </div>

        <div className="flex justify-center">
          <ChatInterface creatorId="test_creator_123" />
        </div>
      </div>
    </main>
  );
}
