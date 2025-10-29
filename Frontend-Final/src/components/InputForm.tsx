import { useState } from 'react';
import { Droplets, Sprout, Calendar, MapPin } from 'lucide-react';

interface InputFormProps {
  onSubmit: (data: FormData) => void;
}

export interface FormData {
  crop: string;
  soilType: string;
  sowingDate: string;
  latitude: number;
  longitude: number;
  farmArea: number;
}

export default function InputForm({ onSubmit }: InputFormProps) {
  const [crop, setCrop] = useState('');
  const [soilType, setSoilType] = useState('');
  const [sowingDate, setSowingDate] = useState('');
  const [latitude, setLatitude] = useState('');
  const [longitude, setLongitude] = useState('');
  const [farmArea, setFarmArea] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (crop && soilType && sowingDate && latitude && longitude && farmArea) {
      onSubmit({
        crop,
        soilType,
        sowingDate,
        latitude: parseFloat(latitude),
        longitude: parseFloat(longitude),
        farmArea: parseFloat(farmArea)
      });
    }
  };

  const isFormValid = crop && soilType && sowingDate && latitude && longitude && farmArea;

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-gray-50 flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-lg p-8">
          <div className="flex items-center justify-center mb-8">
            <div className="bg-green-500 p-4 rounded-xl">
              <Droplets className="w-10 h-10 text-white" />
            </div>
          </div>

          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">PrAgIS</h1>
            <p className="text-sm text-gray-600">Multi-Agent Precision Irrigation System</p>
            <p className="text-xs text-gray-500 mt-2">Enter your farm details to get started</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="crop" className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                <Sprout className="w-4 h-4 text-green-600" />
                Crop Type
              </label>
              <select
                id="crop"
                value={crop}
                onChange={(e) => setCrop(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none transition-all"
                required
              >
                <option value="">Select crop type</option>
                <option value="wheat">Wheat</option>
                <option value="rice">Rice</option>
                <option value="maize">Maize</option>
              </select>
            </div>

            <div>
              <label htmlFor="soilType" className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                <MapPin className="w-4 h-4 text-green-600" />
                Soil Type
              </label>
              <select
                id="soilType"
                value={soilType}
                onChange={(e) => setSoilType(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none transition-all"
                required
              >
                <option value="">Select soil type</option>
                <option value="sandy">Alluvial Soil</option>
                <option value="clay">Black Soil</option>
                <option value="sandy">Red Soil</option>
              </select>
            </div>

            <div>
              <label htmlFor="sowingDate" className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                <Calendar className="w-4 h-4 text-green-600" />
                Sowing Date
              </label>
              <input
                type="date"
                id="sowingDate"
                value={sowingDate}
                onChange={(e) => setSowingDate(e.target.value)}
                max={new Date().toISOString().split('T')[0]}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none transition-all"
                required
              />
            </div>

            <div>
              <label htmlFor="latitude" className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                <MapPin className="w-4 h-4 text-green-600" />
                Latitude
              </label>
              <input
                type="number"
                id="latitude"
                value={latitude}
                onChange={(e) => setLatitude(e.target.value)}
                step="0.000001"
                placeholder="e.g. 28.7041"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none transition-all"
                required
              />
            </div>

            <div>
              <label htmlFor="longitude" className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                <MapPin className="w-4 h-4 text-green-600" />
                Longitude
              </label>
              <input
                type="number"
                id="longitude"
                value={longitude}
                onChange={(e) => setLongitude(e.target.value)}
                step="0.000001"
                placeholder="e.g. 77.1025"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none transition-all"
                required
              />
            </div>

            <div>
              <label htmlFor="farmArea" className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                <MapPin className="w-4 h-4 text-green-600" />
                Farm Area (hectares)
              </label>
              <input
                type="number"
                id="farmArea"
                value={farmArea}
                onChange={(e) => setFarmArea(e.target.value)}
                step="0.1"
                min="0.1"
                placeholder="e.g. 2.5"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none transition-all"
                required
              />
            </div>

            <button
              type="submit"
              disabled={!isFormValid}
              className={`w-full py-3 px-4 rounded-lg font-semibold text-white transition-all ${
                isFormValid
                  ? 'bg-green-500 hover:bg-green-600 active:scale-95'
                  : 'bg-gray-300 cursor-not-allowed'
              }`}
            >
              Generate Irrigation Plan
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-gray-500 mt-6">
          Powered by multi-agent AI for precision agriculture
        </p>
      </div>
    </div>
  );
}
