import React, { useState } from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import './MakeSchedule.css';
import { useNavigate } from 'react-router-dom';

function MakeSchedule(){
    const navigate = useNavigate();
    const [selectedDate, setSelectedDate] = useState(null);
    const [additionalInfo, setAdditionalInfo] = useState('');
    const goBack = () => {
        window.history.back();
    }
    const goResult = () => {
        navigate('/result');
    }
  return (
    <div className="container">
      <div className="title">일정 자동 생성</div>
      <div className="content-row1">
        <div className="label">날짜</div>
        <div className="date-picker">
          <DatePicker
            selected={selectedDate}
            onChange={(date) => setSelectedDate(date)}
            placeholderText="날짜 선택"
            dateFormat="yyyy/MM/dd"
          />
        </div>
      </div>
      <div className="content-row1">
        <div className="label">추가정보</div>
        <textarea className="text-box" placeholder="요청사항을 적어주세요" value={additionalInfo}
          onChange={(e) => setAdditionalInfo(e.target.value)}></textarea>
      </div>
      <div className='make-gap'>
        <button className='back-button' onClick={goBack}>뒤로가기</button>
        <button className="generate-button" onClick={goResult}>생성버튼</button>
      </div>
    </div>
  );
}
export default MakeSchedule;