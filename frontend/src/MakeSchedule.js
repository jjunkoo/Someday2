import React, { useState } from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import './MakeSchedule.css';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import CheckboxGroup from './CheckboxGroup';
function MakeSchedule(){
    const navigate = useNavigate();
    const [selectedDate, setSelectedDate] = useState(null);
    const options = [
      { id: "option1", name: "점심식사" },
      { id :"option2", name: "저녁식사"},
      { id: "option3", name: "운동" },
      { id: "option4", name: "공부" },
      { id: "option5", name: "스포츠" },
      { id: "option6", name: "관람" },
      { id: "option7", name: "공원" },
      { id: "option8", name: "실내활동" },
    ];
  
    const [groupSelections, setGroupSelections] = useState({
      group1: [],
      group2: [],
    });
    // ID -> 라벨 값으로 변환하는 함수
    const mapIdsToLabels = (ids) => {
      return ids.map((id) => {
          const option = options.find((opt) => opt.id === id);
          return option ? option.name : id; // 해당 ID에 대한 라벨 반환
      });
  };
    // 각 그룹의 선택 상태 업데이트
    const handleGroupChange = (groupName, selections) => {
      setGroupSelections((prev) => ({
        ...prev,
        [groupName]: selections,
      }));
    };
    const goBack = () => {
        window.history.back();
    }
    const goResult = () => {
      const dataToSend = {
        date: selectedDate,
        selection: {
            group1: mapIdsToLabels(groupSelections.group1),
            group2: mapIdsToLabels(groupSelections.group2),
        },
    };
      axios.post('http://localhost:8000/api/make_schedule/', dataToSend, { withCredentials: true })
      .then(response => {
        if (response.data.status === 'success') {
          alert('일정이 생성되었습니다');
          navigate("/result", { state: { result: response.data.result, date : selectedDate } });
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
        <div className = "selectgroup">
          <div>
            일정에 들어가지 않았으면 하는 활동을
            골라주세요(최대 2개)
          </div>
          <CheckboxGroup
            title="제외활동"
            maxSelections={2}
            options={options}
            onSelectionChange={(selections) =>
              handleGroupChange("group2", selections)
            }
          />
        </div>
      </div>
      <div className="make-gap">
        <button className="back-button" onClick={goBack}>
          뒤로가기
        </button>
        <button className="generate-button" onClick={goResult}>
          생성버튼
        </button>
      </div>
    </div>
  );
}
export default MakeSchedule;