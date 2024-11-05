import { useNavigate } from "react-router-dom";
import "./PlaceList.css"
import { useState } from "react";
function PlaceList(){
    const [isModalOpen, setIsModalOpen] = useState(false);

    const openModal = () => {
        setIsModalOpen(true);
    };

    const closeModal = () => {
        setIsModalOpen(false);
    };
    const navigate = useNavigate();
    const goBack = () => {
        window.history.back();
    }
    return(
        <div className="container">
      <div className="header">맞춤 장소 리스트</div>
      <div className="content-row2">
        <div className="box1">종류</div>
        <div className="box2">장소 정보</div>
      </div>
      <div className="content-row2">
        <div className="box1">놀이공원</div>
        <div className="box2">롯데월드 - 서울 송파구 올림픽로 240</div>
        <button className="box3" onClick={openModal}>지도</button>
      </div>
      <div className="content-row2">
        <div className="box1">놀이공원</div>
        <div className="box2">어린이대공원 - 서울 광진구 능동로 216</div>
        <button className="box3" onClick={openModal}>지도</button>
      </div>
      {isModalOpen && (
        <div className="modal-overlay">
          <div className="modal1">
            <h2>지도 정보</h2>
            <p>여기에 지도의 내용을 넣을 수 있습니다.</p>
            <button className="close-button" onClick={closeModal}>닫기</button>
          </div>
        </div>
      )}
      <button className="back-button" onClick={goBack}>뒤로가기</button>
    </div>
  );
};
export default PlaceList;