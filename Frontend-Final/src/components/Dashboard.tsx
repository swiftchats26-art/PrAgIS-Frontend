import Header from './Header';
import FarmSummary from './FarmSummary';
import AgentOutputs from './AgentOutputs';
import IrrigationSchedule from './IrrigationSchedule';
import Explanation from './Explanation';
import type { FormData } from './InputForm';

interface DashboardProps {
  farmData: FormData;
}

export default function Dashboard({ farmData }: DashboardProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <FarmSummary farmData={farmData} />
          </div>

          <div className="lg:col-span-2">
            <AgentOutputs />
          </div>

          <div className="lg:col-span-2">
            <IrrigationSchedule />
          </div>

          <div className="lg:col-span-1">
            <Explanation />
          </div>
        </div>
      </main>
    </div>
  );
}
