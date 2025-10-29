import { useIrrigationSchedule } from '../hooks/useData';
import type { IrrigationData } from '../types/irrigation';

export default function IrrigationSchedule() {
  const data = useIrrigationSchedule() as IrrigationData;
  
  console.log('IrrigationSchedule received data:', data);
  
  const confidenceColor =
    data.overallConfidence > 80 ? 'bg-green-500' :
    data.overallConfidence > 50 ? 'bg-yellow-400' :
    'bg-red-500';

  return (
    <section className="bg-white rounded-xl shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Irrigation Schedule</h2>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">Overall Confidence</span>
          <span className={`${confidenceColor} text-white text-sm font-bold px-3 py-1 rounded-full`}>
            {data.overallConfidence}%
          </span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Days After Sowing</th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Irrigation Volume (mm)</th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Irrigation Mode</th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Yield Index</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
              <td className="py-3 px-4 text-sm text-gray-900">{data.daysAfterSowing}</td>
              <td className="py-3 px-4 text-sm font-medium text-gray-900">{typeof data.irrigationVolume === 'number' ? (data.irrigationVolume === 0 ? 'No irrigation needed' : data.irrigationVolume.toFixed(2)) : 'N/A'}</td>
              <td className="py-3 px-4">
                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-green-50 text-green-700">
                  {data.irrigationMode || 'N/A'}
                </span>
              </td>
              <td className="py-3 px-4 text-sm font-medium text-gray-900">{(data.yieldIndex * 100).toFixed(1)}%</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  );
}
