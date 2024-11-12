import { useNavigate } from "react-router-dom";
import "./PlaceList.css";
import { useState, useEffect, useRef } from "react";
import axios from "axios";

function PlaceList() {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedAddress, setSelectedAddress] = useState("");
    const [placeDetails, setPlaceDetails] = useState(null);
    const mapRef = useRef(null);

    const openModal = (address) => {
        setSelectedAddress(address);
        setIsModalOpen(true);
    };

    const closeModal = () => {
        setIsModalOpen(false);
        setPlaceDetails(null);
    };

    const navigate = useNavigate();
    const goBack = () => {
        window.history.back();
    };

    useEffect(() => {
        const loadGoogleMaps = () => {
            return new Promise((resolve, reject) => {
                if (document.getElementById("google-maps-script")) {
                    resolve();
                    return;
                }

                const script = document.createElement("script");
                script.id = "google-maps-script";
                script.src = `https://maps.googleapis.com/maps/api/js?key=AIzaSyDafexznD1Asfj5h6ScRBzDYmZqC2H59yI&libraries=places`;
                script.async = true;
                script.onload = () => resolve();
                script.onerror = () => reject(new Error("Failed to load the Google Maps script."));
                document.head.appendChild(script);
            });
        };

        const initializeMap = async () => {
            try {
                await loadGoogleMaps();

                if (!mapRef.current) {
                    console.error("Map container (mapRef) is not initialized.");
                    return;
                }

                const service = new window.google.maps.places.PlacesService(mapRef.current);
                const request = {
                    query: selectedAddress,
                    fields: ["name", "geometry", "formatted_address", "rating", "opening_hours", "place_id"],
                };

                service.findPlaceFromQuery(request, (results, status) => {
                    if (status === window.google.maps.places.PlacesServiceStatus.OK && results[0]) {
                        const place = results[0];
                        setPlaceDetails({
                            name: place.name,
                            address: place.formatted_address,
                            rating: place.rating || "정보 없음",
                            hours: place.opening_hours ? place.opening_hours.weekday_text : ["영업시간 정보 없음"],
                            placeId: place.place_id,
                        });

                        const map = new window.google.maps.Map(mapRef.current, {
                            center: place.geometry.location,
                            zoom: 14,
                        });

                        new window.google.maps.Marker({
                          position: place.geometry.location,
                          map: map,
                      });                      
                    } else {
                        console.error("장소 검색에 실패했습니다.");
                    }
                });
            } catch (error) {
                console.error("지도 초기화 중 에러 발생:", error);
            }
        };

        if (isModalOpen && selectedAddress) {
            initializeMap();
        }

        return () => {
            setPlaceDetails(null);
        };
    }, [isModalOpen, selectedAddress]);

    return (
        <div className="container">
            <div className="header">맞춤 장소 리스트</div>
            <div className="content-row2">
                <div className="box1">종류</div>
                <div className="box2">장소 정보</div>
            </div>
            <div className="content-row2">
                <div className="box1">놀이공원</div>
                <div className="box2">롯데월드 - 서울 송파구 올림픽로 240</div>
                <button className="box3" onClick={() => openModal("롯데월드 서울 송파구 올림픽로 240")}>지도</button>
            </div>
            <div className="content-row2">
                <div className="box1">놀이공원</div>
                <div className="box2">어린이대공원 - 서울 광진구 능동로 216</div>
                <button className="box3" onClick={() => openModal("어린이대공원 서울 광진구 능동로 216")}>지도</button>
            </div>
            {isModalOpen && (
                <div className="modal-overlay">
                    <div className="modal1">
                        <h2>지도 정보</h2>
                        <div ref={mapRef} style={{ width: "400px", height: "300px" }}></div>
                        {placeDetails && (
                          <div className="place-details">
                          <p>이름: {placeDetails.name}</p>
                          <p>주소: {placeDetails.address}</p>
                          <p>평점: {placeDetails.rating}</p>
                          <p>영업시간:</p>
                          <ul>
                          {placeDetails.hours ? (
                          placeDetails.hours.map((hour, index) => (
                          <li key={index}>{hour}</li>
                          ))
                        ) : (
              <li>영업시간 정보 없음</li>
            )}
        </ul>
        <a href={`https://www.google.com/maps/place/?q=place_id:${placeDetails.placeId}`} target="_blank" rel="noopener noreferrer">Google 지도에서 보기</a>
    </div>
)}

                        <button className="close-button" onClick={closeModal}>닫기</button>
                    </div>
                </div>
            )}
            <button className="back-button" onClick={goBack}>뒤로가기</button>
        </div>
    );
}

export default PlaceList;
