import { addHours, format } from "date-fns";
import React, { useState } from "react";
import "./CalendarModal.css";

const Modal = ({ event, slot, onClose, onSave , onDelete }) => {
  const [id, setId] = useState(event ? event.id : "")
  const [title, setTitle] = useState(event ? event.title : "");
  const [start, setStart] = useState(event ? event.start : slot.start);
  const [end, setEnd] = useState(event ? event.end : new Date(slot.start.getTime() + 60 * 60 * 1000));
  const [description,setDescription] = useState(event? event.description : "");
  const handleSave = () => {
    onSave({
      ...event,
      title,
      start,
      end,
      description 
    });
  };

  const handleDelete = () => {
    onDelete({
        ...event,
        id,
        title,
        start,
        end,
        description
    });
  }


  const displayStart = format(new Date(start), "yyyy-MM-dd'T'HH:mm");
  const displayEnd = format(new Date(end), "yyyy-MM-dd'T'HH:mm");
  return (
    <div className="modal-overlay">
        <div className="modal-container">
            <div className="modal-header">
                {event ? <h3>이벤트 수정</h3> : <h3>이벤트 추가</h3>}
            </div>
            <div className="modal-body">
                <label className="modal-label">
                    제목:
                    <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    className="modal-input"
                    />
                </label>
                <label className="modal-label">
                    내용:
                    <input
                    type="text"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    className="modal-input"
                    />
                </label>
                <label className="modal-label">
                    시작 시간:
                    <input
                    type="datetime-local"
                    value={displayStart}
                    onChange={(e) => setStart(new Date(e.target.value))}
                    className="modal-input"
                    />
                </label>
                <label className="modal-label">
                    종료 시간:
                    <input
                    type="datetime-local"
                    value={displayEnd}
                    onChange={(e) => setEnd(new Date(e.target.value))}
                    className="modal-input"
                    />
                </label>
            </div>
            <div className="modal-footer">
                <button onClick={handleSave} className="modal-button save-button">
                    저장
                </button>
                <button onClick={handleDelete} className="modal-button cancel-button">
                    삭제
                </button>
                <button onClick={onClose} className="modal-button cancel-button">
                    닫기
                </button>
            </div>
        </div>
    </div>
  );
};
export default Modal;