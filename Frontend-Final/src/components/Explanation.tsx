import { Lightbulb, Droplets } from 'lucide-react';
import { useExplanation } from '../hooks/useData';

export default function Explanation() {
  const data = useExplanation();

  return (
    <section className="bg-white rounded-xl shadow-sm p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Explanation</h2>

      <div className="space-y-4">
        <div className="flex gap-3">
          <Lightbulb className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-gray-700 leading-relaxed">
            {data.reasoning}
          </p>
        </div>

        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <Droplets className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-semibold text-green-900 mb-1">Water Savings</h3>
              <p className="text-sm text-green-800">{data.waterSaved}</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
