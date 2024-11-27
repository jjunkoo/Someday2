import { useState } from "react";
import "./ResultPage.css"
function ResultPage(){
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [rating, setRating] = useState(0); // 별점 상태를 위한 state
    const [selectedOption, setSelectedOption] = useState(null);
    const [feedbackText, setFeedbackText] = useState(''); // 피드백 텍스트 상태

    const [savedRating, setSavedRating] = useState(null); // 저장된 별점
    const [savedFeedback, setSavedFeedback] = useState(''); // 저장된 피드백 텍스트
  const handleFeedbackClick = () => {
    // 모달을 열 때, 이전에 저장된 데이터를 rating과 feedbackText에 설정
    setRating(savedRating || 0);
    setFeedbackText(savedFeedback || '');
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setSavedRating(rating);
    setSavedFeedback(feedbackText);
    // 모달 닫기
    setIsModalOpen(false);
  };

  const handleStarClick = (index) => {
    setRating(index + 1); // 선택된 별과 왼쪽의 모든 별 채우기
  };

  const handleOXClick = (option) => {
    setSelectedOption(option); // 선택한 옵션을 저장 ("O" 또는 "X")
  };

  const handlePageReload = () => {
    window.location.reload(); // 페이지 새로고침
  };

  const goBack = () => {
    window.history.back();
  }

  return (
    <div className="container">
      <div className="title">일정 자동 생성</div>
      <div className="content-row">
        <div className="box1">날짜 시간</div>
        <div className="box1">일정 이름</div>
        <div className="box">내용</div>
      </div>
      <div className="content-row">
        <div className="time-box">24/11/02 09:00:00 ~ 24/11/02 12:00:00</div>
        <div className="name-box">등산</div>
        <div className="cbox">OO산에서 등산</div>
        <div className="ox-buttons">
          <button
            className={`ox-button ${selectedOption === 'O' ? 'selected' : ''}`}
            onClick={() => handleOXClick('O')}
          >
            👍
          </button>
          <button
            className={`ox-button ${selectedOption === 'X' ? 'selected' : ''}`}
            onClick={() => handleOXClick('X')}
          >
            👎
          </button>
        </div>
      </div>
      <div className="content-row">
        <div className="time-box">24/11/02 12:00:00 ~ 24/11/02 13:00:00</div>
        <div className="name-box">점심식사</div>
        <div className="cbox">OOO에서 점심식사</div>
        <div className="ox-buttons">
          <button
            className={`ox-button ${selectedOption === 'O' ? 'selected' : ''}`}
            onClick={() => handleOXClick('O')}
          >
            👍
          </button>
          <button
            className={`ox-button ${selectedOption === 'X' ? 'selected' : ''}`}
            onClick={() => handleOXClick('X')}
          >
            👎
          </button>
        </div>
      </div>
      <div className="content-row">
        <div className="time-box">24/11/02 08:00:00 ~ 24/11/02 09:00:00</div>
        <div className="name-box">아침식사</div>
        <div className="cbox">OOO에서 아침식사</div>
        <div className="ox-buttons">
          <button
            className={`ox-button ${selectedOption === 'O' ? 'selected' : ''}`}
            onClick={() => handleOXClick('O')}
          >
            👍
          </button>
          <button
            className={`ox-button ${selectedOption === 'X' ? 'selected' : ''}`}
            onClick={() => handleOXClick('X')}
          >
            👎
          </button>
        </div>
      </div>
      <div>
        <button className="feedback-button" onClick={handleFeedbackClick}>피드백 버튼</button>
        </div>
      <div className="button-row">
        <button className = "schedule-button" onClick = {goBack}> 뒤로가기</button>
        <button className="schedule-button">일정 저장</button>
        <button className="schedule-button" onClick = {handlePageReload}>일정 재생성</button>
      </div>

      {isModalOpen && (
        <div className="modal">
          <div className="modal-content">
            <p>위의 일정에 만족하십니까?</p>
            <div className="stars">
              {[...Array(5)].map((_, index) => (
                <span
                  key={index}
                  className={index < rating ? 'star filled' : 'star'}
                  onClick={() => handleStarClick(index)}
                >
                  ★
                </span>
              ))}
            </div>
            <textarea
              className="feedback-textarea"
              placeholder="피드백 입력"
              value={feedbackText}
              onChange={(e) => setFeedbackText(e.target.value)}
            ></textarea>
            <button className="close-modal-button" onClick={handleCloseModal}>닫기</button>
          </div>
        </div>
      )}
    </div>
  );
}
export default ResultPage;