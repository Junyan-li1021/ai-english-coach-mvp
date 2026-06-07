interface ScoreCardProps {
  label: string;
  score: number;
  maxScore?: number;
}

function ScoreBar({ label, score, maxScore = 100 }: ScoreCardProps) {
  const pct = Math.min((score / maxScore) * 100, 100);
  const color =
    pct >= 80 ? 'bg-green-500' : pct >= 60 ? 'bg-yellow-500' : 'bg-red-500';

  return (
    <div className="mb-4">
      <div className="flex justify-between items-center mb-1">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <span className="text-sm font-bold text-gray-900">
          {score}/{maxScore}
        </span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2.5">
        <div
          className={`h-2.5 rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

interface Scores {
  accuracy: number;
  fluency: number;
  overall: number;
  feedback: string;
}

interface ScoreCardGroupProps {
  scores: Scores;
}

export default function ScoreCard({ scores }: ScoreCardGroupProps) {
  return (
    <div className="bg-white rounded-xl shadow-md p-6">
      <h3 className="text-lg font-bold text-gray-800 mb-4">评分报告</h3>
      <ScoreBar label="内容准确度" score={scores.accuracy} />
      <ScoreBar label="表达流利度" score={scores.fluency} />
      <ScoreBar label="综合评分" score={scores.overall} />
      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
        <p className="text-sm text-gray-600">
          <span className="font-medium">总评：</span>{scores.feedback}
        </p>
      </div>
    </div>
  );
}

export { ScoreBar };
