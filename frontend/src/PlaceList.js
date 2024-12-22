import React, { useState } from "react";
import { useLocation } from "react-router-dom";

const PlaceList = () => {
  const [keyword, setKeyword] = useState("");
  const [places, setPlaces] = useState([]);
  const location = useLocation();
  const category = location.state?.category;
  // 장소 검색 함수
  const findMostFrequent = (array) => {
    if (!array || array.length === 0) return null;

    const frequencyMap = array.reduce((acc, item) => {
      acc[item] = (acc[item] || 0) + 1; // 빈도 계산
      return acc;
    }, {});

    // 가장 많이 나온 텍스트 찾기
    let mostFrequent = null;
    let maxCount = 0;
    for (const [item, count] of Object.entries(frequencyMap)) {
      if (count > maxCount) {
        maxCount = count;
        mostFrequent = item;
      }
    }

    return mostFrequent;
  };
  const handleSearch = () => {
    if (!keyword.trim()) {
      alert("검색어를 입력해주세요!");
      return;
    }
    // 가장 많이 나온 카테고리 계산
    
    const ps = new window.kakao.maps.services.Places();
    ps.keywordSearch(keyword, (data, status) => {
      if (status === window.kakao.maps.services.Status.OK) {
        setPlaces(data);
      } else {
        alert("검색 결과가 없습니다.");
      }
    });
  };

  // 카테고리 기반 추천 검색어
  const handleRecommendSearch = () => {
    const mostFrequentText = findMostFrequent(category);
    let recommendedKeyword = "";
    switch (mostFrequentText) {
      case "점심식사":
        recommendedKeyword = "광진구 맛집";
      case "저녁식사":
        recommendedKeyword = "광진구 맛집";
        break;
      case "운동":
        recommendedKeyword = "광진구 헬스장";
        break;
      case "공부":
        recommendedKeyword = "광진구 스터디카페";
        break;
      case "스포츠":
        recommendedKeyword = "광진구 스포츠센터";
        break;
      case "관람":
        recommendedKeyword = "광진구 영화관";
        break;
      case "공원":
        recommendedKeyword = "광진구 공원";
        break;
      case "실내활동":
        recommendedKeyword = "광진구 방탈출카페";
        break;
      default:
        alert("추천 검색어를 생성할 카테고리가 없습니다.");
        return;
    }
    setKeyword(recommendedKeyword);
  };

  return (
    <div className="search-section">
      <h2>장소 검색</h2>
      <div className="search-buttons-container">
        <input
          type="text"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          placeholder="검색어를 입력하세요"
        />
        <button onClick={handleSearch}>검색</button>
        <button className="recommend-button" onClick={handleRecommendSearch}>
          검색어 추천
        </button>
      </div>
      <ul>
        {places.map((place, index) => (
          <li key={index}>
            <strong>{place.place_name}</strong>
            <p>{place.address_name}</p>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default PlaceList;