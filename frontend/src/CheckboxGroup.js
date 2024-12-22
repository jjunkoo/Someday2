import React, { useState } from "react";
import "./CheckboxGroup.css";
function CheckboxGroup({ title, maxSelections, options, onSelectionChange }) {
  const [checkboxes, setCheckboxes] = useState(
    options.reduce((acc, option) => {
      acc[option.id] = false; // 초기 상태 false
      return acc;
    }, {})
  );

  // 체크박스 변경 핸들러
  const handleCheckboxChange = (event) => {
    const { name, checked } = event.target;

    // 선택된 체크박스 개수 확인
    const selectedCount = Object.values(checkboxes).filter(Boolean).length;

    // 선택 가능한 개수 초과 시, 새로운 선택을 막음
    if (checked && selectedCount >= maxSelections) {
      alert(`최대 ${maxSelections}개까지 선택 가능합니다.`);
      return;
    }

    // 상태 업데이트
    const updatedCheckboxes = {
      ...checkboxes,
      [name]: checked,
    };

    setCheckboxes(updatedCheckboxes);

    // 선택된 항목만 부모로 전달
    const selectedOptions = Object.entries(updatedCheckboxes)
      .filter(([_, value]) => value) // true인 항목만 필터링
      .map(([key]) => key); // 선택된 항목의 id만 반환

    onSelectionChange(selectedOptions);
  };

  return (
    <div className="checkbox-group">
      <h3 className="checkbox-group-title">{title}</h3>
      <div className="checkbox-options">
        {options.map((option) => (
          <label key={option.id} className="checkbox-label">
            <input
              type="checkbox"
              name={option.id}
              checked={checkboxes[option.id]}
              onChange={handleCheckboxChange}
              className="checkbox-input"
            />
            {option.name}
          </label>
        ))}
      </div>
    </div>
  );
}

export default CheckboxGroup;
