import React, { useState } from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import './MakeSchedule.css';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

function MakeSchedule(){
    const navigate = useNavigate();
    const [selectedDate, setSelectedDate] = useState(null);
    const [additionalInfo, setAdditionalInfo] = useState('');
    const goBack = () => {
        window.history.back();
    }
    const goResult = () => {
      axios.post('http://localhost:8000/api/make_schedule/', {date : selectedDate}, { withCredentials: true })
      .then(response => {
        if (response.data.status === 'success') {
          alert('일정이 생성되었습니다');
          navigate("/result", { state: { result: response.data.result } });
        } else {
          alert(`오류: ${response.data.message}`);
        }
      })
      .catch(error => {
        console.error('일정 생성 중 오류 발생', error);
        alert('일정 생성 중 오류가 발생하였습니다');
      });
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