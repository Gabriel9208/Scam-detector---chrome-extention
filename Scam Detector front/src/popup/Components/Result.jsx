import { useContext, useMemo } from 'react'
import { GlobalContext } from '../Popup.jsx'
import { CircularProgressbar, buildStyles } from 'react-circular-progressbar'
import 'react-circular-progressbar/dist/styles.css'
import { scoreContributions } from './Analysis.jsx'

export const Result = () => {
  const { riskScore, loading, error } = useContext(GlobalContext);

  const getColor = (score) => {
    if (score > 2) return '#FF0000';
    if (score > 1) return '#FFA500';
    return '#00FF00';
  }

  const getText = (score) => {
    if (score > 2) return '惡意';
    if (score > 1) return '可疑';
    return '安全';
  }

  const maxScore = useMemo(() => {
    return Object.values(scoreContributions).reduce((sum, value) => sum + value, 0);
  }, []);

  const normalizedScore = useMemo(() => {
    return 100 - (riskScore / maxScore) * 100;
  }, [riskScore]);

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
        text: getText(riskScore),
        color: getColor(riskScore),
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