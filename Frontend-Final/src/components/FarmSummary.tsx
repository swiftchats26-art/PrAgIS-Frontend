import { Wheat, Sprout, MapPin, Calendar } from 'lucide-react';
import { useFarmSummary } from '../hooks/useData';
import type { FormData } from './InputForm';

const cropIcons: Record<string, any> = {
  Wheat: Wheat,
  Maize: Sprout,
  Rice: Sprout
};

interface FarmSummaryProps {
  farmData: FormData;
}

export default function FarmSummary({ farmData }: FarmSummaryProps) {
  const data = useFarmSummary();

  const getCropIcon = (cropName: string) => {
    return cropIcons[cropName] || Sprout;
  };

  const CropIcon = getCropIcon(farmData.crop);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <section className="bg-white rounded-xl shadow-sm p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Farm Summary</h2>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Total Area</span>
          <span className="text-lg font-semibold text-gray-900">{farmData.farmArea} ha</span>
        </div>

        <div>
          <span className="text-sm text-gray-600 block mb-2">Crop Type</span>
          <div className="flex gap-3">
            <div className="flex items-center gap-2 bg-green-50 px-3 py-2 rounded-lg border border-green-200">
              <CropIcon className="w-4 h-4 text-green-600" />
              <span className="text-sm font-medium text-gray-900">{farmData.crop}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MapPin className="w-4 h-4 text-gray-500" />
            <span className="text-sm text-gray-600">Soil Type</span>
          </div>
          <span className="text-sm font-medium text-gray-900">{farmData.soilType}</span>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-gray-500" />
            <span className="text-sm text-gray-600">Sowing Date</span>
          </div>
          <span className="text-sm font-medium text-gray-900">{formatDate(farmData.sowingDate)}</span>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-gray-500" />
            <span className="text-sm text-gray-600">Last Run</span>
          </div>
          <span className="text-sm font-medium text-gray-900">{data.lastRun}</span>
        </div>

        <div className="pt-4 border-t border-gray-100">
          <span className="text-xs font-medium text-gray-700 block mb-2">Confidence Legend</span>
          <div className="flex gap-4 text-xs">
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full bg-green-500"></div>
              <span className="text-gray-600">&gt;80%</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full bg-yellow-400"></div>
              <span className="text-gray-600">50-80%</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full bg-red-500"></div>
              <span className="text-gray-600">&lt;50%</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
