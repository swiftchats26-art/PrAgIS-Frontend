import { Droplets } from 'lucide-react';

export default function Header() {
  const currentDate = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="bg-green-500 p-2 rounded-lg">
            <Droplets className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">PrAgIS</h1>
            <p className="text-sm text-gray-600">Multi-Agent Precision Irrigation System</p>
          </div>
        </div>
        <div className="text-sm text-gray-600">
          {currentDate}
        </div>
      </div>
    </header>
  );
}
