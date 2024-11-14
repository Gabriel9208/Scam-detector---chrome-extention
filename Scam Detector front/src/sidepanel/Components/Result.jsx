import { useContext, useMemo } from 'react'
import { GlobalContext } from '../GlobalProvider.jsx'
import { CircularProgressbar, buildStyles } from 'react-circular-progressbar'
import 'react-circular-progressbar/dist/styles.css'
import { scoreContributions } from './Analysis.jsx'

export const Result = ({threshold}) => {
  const { riskScore, loading, error } = useContext(GlobalContext);

  const color = useMemo(() => {
    if (riskScore > 2) return '#FF0000';
    if (riskScore > threshold) return '#FFA500';
    return '#00FF00';
  }, [threshold, riskScore])

  const text = useMemo(() => {
    if (riskScore > 2) return '惡意';
    if (riskScore > threshold) return '可疑';
    return '安全';
  }, [threshold, riskScore])

  const normalizedScore = useMemo(() => {
    let score;
    if (riskScore > 2) {
      score = 0; 
    } else if (riskScore > threshold) {
      const suspiciousRange = (2 - threshold);
      const position = (2 - riskScore) / suspiciousRange;
      score = 30 + (position * 30);
    } else {
      const position = (threshold - riskScore) / threshold;
      score = 90 + (position * 15);
    }
    return Math.max(0, Math.min(100, score)); 
  }, [riskScore, threshold]);
    

  const renderContent = useMemo(() => {
    if (loading) {
      return {
        value: 100,
        text: '載入中...',
        color: '#6b7280',
        className: 'loading-spin'
      };
    } else if (error) {
      return {
        value: 100,
        text: '載入失敗',
        color: '#DC2626',
        className: ''
      };
    } else {
      return {
        value: normalizedScore,
        text: text,
        color: color,
        className: ''
      };
    }
  }, [normalizedScore, loading, error, riskScore]);

  return (
    <div className='result-container'>
      <div style={{ width: '200px', height: '200px' }} className={renderContent.className}>
        <CircularProgressbar
          value={renderContent.value}
          text={renderContent.text}
          counterClockwise={true}
          styles={buildStyles({
            rotation: loading ? 1 : 0,
            strokeLinecap: 'butt',
            textSize: '16px',
            pathTransitionDuration: 0.5,
            pathColor: renderContent.color,
            textColor: renderContent.color,
            trailColor: '#d6d6d6',
          })}
        />
      </div>
    </div>
  )
}