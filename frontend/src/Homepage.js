import axios from "axios";
import { useEffect, useState } from "react";
import CalendarAuth from "./CalanderEvents";
import { redirect, useNavigate } from "react-router-dom";
import "./Homepage.css"

function Homepage(){
    const [modelStatus, setModelStatus] = useState('not_trained'); 
    const navigate = useNavigate();
    const goList = () => {
        navigate("/list");
    }
    const goMake = () => {
        navigate("/make");
    }
    const goRefresh = () => {
        axios.post('http://localhost:8000/api/refresh/', {}, { withCredentials: true })
        .then(response => {
          if (response.data.status === 'success') {
            alert('이벤트가 성공적으로 새로고침되었습니다.');
            window.location.reload();
          } else {
            alert(`오류: ${response.data.message}`);
          }
        })
        .catch(error => {
          console.error('이벤트 새로고침 오류:', error);
          alert('이벤트 새로고침 중 오류가 발생했습니다.');
        });
    }
    const checkModelStatus = async () => {
      try {
          const response = await fetch('/api/check_model_status/', {
              method: 'GET',
          });

          const data = await response.json();

          if (response.ok) {
              setModelStatus(data.status);
              if (data.status === 'trained') {
                  alert('모델 학습이 완료되었습니다.');
              } else if (data.status === 'training') {
                  alert('모델 학습이 진행 중입니다.');
              } else {
                  alert('모델 학습에 실패했습니다.');
              }
          } else {
              alert('모델 상태를 확인할 수 없습니다.');
          }
      } catch (error) {
          alert('서버 오류가 발생했습니다.');
      }
  };
      return (
        <div className="container">
            <div className="title1">썸데이</div>
            <div className="calendar">
                <CalendarAuth></CalendarAuth>
            </div>
                <div className="button-group">
                <button className="make-button" onClick={goRefresh}>새로고침</button>
                <button className="make-button" onClick={goMake}>일정 자동 생성</button>
                <button className="list-button" onClick={goList}>맞춤 장소 리스트</button>
                <button className="make-button" onClick={checkModelStatus}>모델 학습 확인</button>
                </div>
            
        </div>
      );
}
export default Homepage;