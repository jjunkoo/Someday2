import React, { useState, useEffect } from "react";
import "./ResultPage.css";
import { useLocation, useNavigate } from "react-router-dom";
import axios from "axios";

const placeMapping = {
  점심식사: [
    { name: "광장시장", address: "서울특별시 종로구 창경궁로 88" },
    { name: "명동교자", address: "서울특별시 중구 명동10길 29" },
    { name: "토속촌 삼계탕", address: "서울특별시 종로구 자하문로5길 5" },
    { name: "우래옥", address: "서울특별시 중구 창경궁로 62-29" },
    { name: "신의주부대찌개", address: "서울특별시 광진구 천호대로112길 13 1층" },
  ],
  저녁식사: [
    { name: "광장시장", address: "서울특별시 종로구 창경궁로 88" },
    { name: "명동교자", address: "서울특별시 중구 명동10길 29" },
    { name: "토속촌 삼계탕", address: "서울특별시 종로구 자하문로5길 5" },
    { name: "우래옥", address: "서울특별시 중구 창경궁로 62-29" },
    { name: "신의주부대찌개", address: "서울특별시 광진구 천호대로112길 13 1층" },
  ],
  운동: [
    { name: "서울올림픽공원", address: "서울특별시 송파구 올림픽로 424" },
    { name: "북한산국립공원", address: "서울특별시 강북구 우이동 산1-1" },
    { name: "한강공원 반포지구", address: "서울특별시 서초구 신반포로11길 40" },
    { name: "서울숲", address: "서울특별시 성동구 성수동1가 678-1" },
    { name: "상암월드컵경기장", address: "서울특별시 마포구 월드컵로 240" },
  ],
  스포츠: [
    { name: "잠실종합운동장", address: "서울특별시 송파구 올림픽로 25" },
    { name: "광진구민체육센터", address: "서울특별시 광진구 자양로 117" },
    { name: "강남스포츠클라이밍센터", address: "서울특별시 강남구 대치동 1010-1" },
    { name: "은평구민체육센터", address: "서울특별시 은평구 진관1로 40" },
    { name: "더베이스캠프", address: "서울특별시 광진구 아차산로 292 지하1층" },
  ],
  관람: [
    { name: "국립중앙박물관", address: "서울특별시 용산구 서빙고로 137" },
    { name: "롯데월드", address: "서울특별시 송파구 올림픽로 240" },
    { name: "서울시립미술관", address: "서울특별시 중구 덕수궁길 61" },
    { name: "예술의전당", address: "서울특별시 서초구 남부순환로 2406" },
    { name: "남산서울타워", address: "서울특별시 용산구 남산공원길 105" },
  ],
  공원: [
    { name: "서울숲공원", address: "서울특별시 성동구 뚝섬로 273" },
    { name: "올림픽공원", address: "서울특별시 송파구 올림픽로 424" },
    { name: "북한산국립공원", address: "서울특별시 강북구 우이동 산1-1" },
    { name: "한강공원 여의도지구", address: "서울특별시 영등포구 여의동로 330" },
    { name: "남산공원", address: "서울특별시 중구 삼일대로 231" },
  ],
  실내활동: [
    { name: "코엑스 아쿠아리움", address: "서울특별시 강남구 영동대로 513" },
    { name: "롯데월드 아쿠아리움", address: "서울특별시 송파구 올림픽로 300" },
    { name: "CGV 용산아이파크몰", address: "용산구 한강대로23길 55" },
    { name: "서울형 키즈카페 마포구 상암점", address: "서울특별시 마포구 상암산로1길 71" },
    { name: "메가박스 성수", address: "서울특별시 성동구 왕십리로 50 메가박스스퀘어" },
  ],
  공부: [
    { name: "서울도서관", address: "서울특별시 중구 세종대로 110" },
    { name: "국립중앙도서관", address: "서울특별시 서초구 반포대로 201" },
    { name: "마포평생학습관", address: "서울특별시 마포구 성산로 128" },
    { name: "강남구립 정다운도서관", address: "서울특별시 강남구 학동로67길 11" },
    { name: "성동구립도서관", address: "서울특별시 성동구 고산자로10길 9" },
  ],
};

const ResultPage = () => {
  const [schedules, setSchedules] = useState([]);
  const [selectedSchedules, setSelectedSchedules] = useState([]);
  const [selectedPlace, setSelectedPlace] = useState(null);
  const location = useLocation();
  const modelCategories = location.state?.result;
  const selectedDate = location.state?.date;
  const navigate = useNavigate();

  const timeSlots = [];
  for (let hour = 8; hour < 24; hour++) {
    const nextHour = hour + 1;
    const start = hour.toString().padStart(2, "0") + ":00";
    const end = nextHour.toString().padStart(2, "0") + ":00";
    timeSlots.push(`${start} - ${end}`);
  }

  const generateSchedules = () => {
    const categories = modelCategories || Object.keys(placeMapping);
    const usedCategories = new Set();
    const usedPlaces = new Set();
    const newSchedules = [];

    for (let category of categories) {
      if (placeMapping[category]) {
        const availablePlaces = placeMapping[category].filter(
          (place) => !usedPlaces.has(place.name)
        );

        if (availablePlaces.length > 0) {
          const randomPlace =
            availablePlaces[Math.floor(Math.random() * availablePlaces.length)];
          usedPlaces.add(randomPlace.name);
          usedCategories.add(category);
          newSchedules.push({
            category,
            place: randomPlace,
            timeSlot: timeSlots[newSchedules.length] || "시간 미정",
          });
        }
      }
    }

    setSchedules(newSchedules);
  };

  useEffect(() => {
    generateSchedules();
  }, []);

  const handlePlaceClick = (place) => {
    setSelectedPlace(place);
    const geocoder = new window.kakao.maps.services.Geocoder();
    geocoder.addressSearch(place.address, (result, status) => {
      if (status === window.kakao.maps.services.Status.OK) {
        const options = {
          center: new window.kakao.maps.LatLng(result[0].y, result[0].x),
          level: 3,
        };
        const map = new window.kakao.maps.Map(
          document.getElementById("floating-map"),
          options
        );
        new window.kakao.maps.Marker({
          map,
          position: new window.kakao.maps.LatLng(result[0].y, result[0].x),
        });
      } else {
        alert("주소를 찾을 수 없습니다.");
      }
    });
  };

  const handleScheduleSelect = (schedule) => {
    setSelectedSchedules((prev) => {
      if (prev.includes(schedule)) {
        return prev.filter((s) => s !== schedule);
      }
      return [...prev, schedule];
    });
  };

  const saveSchedulesToBackend = () => {
    if (selectedSchedules.length === 0) {
      alert("선택된 일정이 없습니다.");
      return;
    }
    const adjustedDate = new Date(selectedDate);
    adjustedDate.setDate(adjustedDate.getDate() + 1);

    // adjustedDate를 YYYY-MM-DD 형식으로 변환
    const formattedDate = adjustedDate.toISOString().split("T")[0];

    const payload = selectedSchedules.map((schedule) => ({
      title: schedule.category,
      description: schedule.place.name,
      start: `${formattedDate}T${schedule.timeSlot.split(" - ")[0]}:00+09:00`,
      end: `${formattedDate}T${schedule.timeSlot.split(" - ")[1]}:00+09:00`,
    }));

    axios.post("http://localhost:8000/api/add/", payload, { withCredentials: true })
      .then((response) => {
        if (response.data.status === "success") {
          alert("일정이 성공적으로 저장되었습니다.");
        } else {
          alert(`오류 발생: ${response.data.message}`);
        }
      })
      .catch((error) => {
        console.error("API 요청 중 오류 발생:", error);
        alert("일정 저장 중 문제가 발생했습니다.");
      });
  };
  const goList = () => {
    navigate("/list",{ state: { category : modelCategories } })
  }
  return (
    <div className="container">
      <h1>일정 추천 ({selectedDate?.toLocaleDateString()})</h1>

      <div className="schedule-table">
        {schedules.map((schedule, index) => (
          <div key={index} className="schedule-row">
            <div className="schedule-cell">
              <input
                type="checkbox"
                checked={selectedSchedules.includes(schedule)}
                onChange={() => handleScheduleSelect(schedule)}
              />
            </div>
            <div className="schedule-cell">{schedule.timeSlot}</div>
            <div className="schedule-cell">{schedule.category}</div>
            <div className="schedule-cell">{schedule.place.name}</div>
            <div className="schedule-cell">
              <button onClick={() => handlePlaceClick(schedule.place)}>지도 보기</button>
            </div>
          </div>
        ))}
      </div>

      <button className="regenerate-button" onClick={generateSchedules}>일정 재생성</button>
      <button className="regenerate-button" onClick={saveSchedulesToBackend}>선택된 일정 저장</button>
      <button className="regenerate-button" onClick={goList}>
        맞춤 장소 보기
      </button>

      {selectedPlace && (
        <div id="floating-map-container" className="floating-map">
          <div className="floating-map-header">{selectedPlace.name}</div>
          <div className="floating-map-address">{selectedPlace.address}</div>
          <div id="floating-map" style={{ width: "100%", height: "400px" }}></div>
          <button onClick={() => setSelectedPlace(null)} className="close-map">닫기</button>
        </div>
      )}
    </div>
  );
};

export default ResultPage;
