import { useAgentOutputs } from '../hooks/useData';

function ConfidenceRing({ confidence }: { confidence: number }) {
  const color = confidence > 80 ? 'text-green-500' : confidence > 50 ? 'text-yellow-400' : 'text-red-500';
  const bgColor = confidence > 80 ? 'bg-green-50' : confidence > 50 ? 'bg-yellow-50' : 'bg-red-50';

  return (
    <div className={`relative w-16 h-16 ${bgColor} rounded-full flex items-center justify-center`}>
      <svg className="w-16 h-16 transform -rotate-90">
        <circle
          cx="32"
          cy="32"
          r="28"
          stroke="currentColor"
          strokeWidth="4"
          fill="none"
          className="text-gray-200"
        />
        <circle
          cx="32"
          cy="32"
          r="28"
          stroke="currentColor"
          strokeWidth="4"
          fill="none"
          strokeDasharray={`${2 * Math.PI * 28}`}
          strokeDashoffset={`${2 * Math.PI * 28 * (1 - confidence / 100)}`}
          className={color}
          strokeLinecap="round"
        />
      </svg>
      <span className={`absolute text-sm font-bold ${color}`}>{confidence}%</span>
    </div>
  );
}

export default function AgentOutputs() {
  const outputs = useAgentOutputs();

  return (
    <section className="bg-white rounded-xl shadow-sm p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Agent Outputs</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {outputs.map((output) => (
          <div key={output.category} className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-start justify-between mb-4">
              <h3 className="font-semibold text-gray-900">{output.category}</h3>
              <ConfidenceRing confidence={output.confidence} />
            </div>

            <div className="space-y-2">
              {output.metrics.map((metric, idx) => (
                <div key={idx} className="flex justify-between items-baseline">
                  <span className="text-sm text-gray-600">{metric.label}</span>
                  <span className="text-sm font-medium text-gray-900">
                    {metric.value} {metric.unit}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
