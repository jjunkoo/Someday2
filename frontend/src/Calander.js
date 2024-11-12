import React, { useState } from 'react';
import { Calendar, dateFnsLocalizer } from 'react-big-calendar';
import {
  format as dateFnsFormat,
  parse as dateFnsParse,
  startOfWeek as dateFnsStartOfWeek,
  getDay as dateFnsGetDay,
} from 'date-fns';
import ko from 'date-fns/locale/ko';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import Modal from './CalendarModal';
import axios from 'axios';

const locales = {
  ko: ko,
};

const localizer = dateFnsLocalizer({
  format: dateFnsFormat,
  parse: dateFnsParse,
  startOfWeek: (date) => dateFnsStartOfWeek(date, { locale: ko }),
  getDay: dateFnsGetDay,
  locales,
});

function MyCalendar({ eventDataArray }) {
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [isModalOpen, setModalOpen] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState(null);

  // eventDataArray가 정의되어 있는지 확인
  const [eventList, setEventList] = useState(
    eventDataArray && Array.isArray(eventDataArray)
      ? eventDataArray.map((eventData) => {
          const startDate = new Date(eventData.start.dateTime);
          const endDate = new Date(eventData.end.dateTime);
          return {
            id: eventData.id,
            title: eventData.summary,
            start: startDate,
            end: endDate,
            description : eventData.description,
            allDay: false, // 필요에 따라 설정
          };
        })
      : []
  );

  if (!eventDataArray || !Array.isArray(eventDataArray)) {
    console.error('eventDataArray가 유효한 배열이 아닙니다.');
    return null;
  }
  const handleSelectSlot = (slotInfo) => {
    setSelectedSlot(slotInfo);
    setSelectedEvent(null);
    setModalOpen(true); // 더블 클릭 시 모달 오픈
  };

  const handleSelectEvent = (event) => {
    setSelectedEvent(event);
    setSelectedSlot(null);
    setModalOpen(true);
  };

  const handleEventUpdate = async (updatedEvent) => {
    try {
      // 이벤트 정보를 백엔드로 전송
      await axios.post('http://localhost:8000/api/update/', updatedEvent,{
        withCredentials: true,  // 쿠키 포함
    });
      if(updatedEvent.id){
      // 프론트엔드 상태 업데이트
        setEventList((prevEvents) =>
          prevEvents.map((event) => (event.id === updatedEvent.id ? updatedEvent : event))
        );
      }
      else{
        axios.post('http://localhost:8000/api/refresh/', {}, { withCredentials: true })
        .then(response => {
          if (response.data.status === 'success') {
            alert('이벤트가 성공적으로 추가되었습니다.');
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
      // 모달 창 닫기
      setModalOpen(false);
    } catch (error) {
      console.error('Error updating event:', error);
      // 에러 처리 로직 (예: 사용자에게 오류 알림)
    }
  };

  const handleEventDelete = async (updatedEvent) => {
    try {
      // 이벤트 정보를 백엔드로 전송
      await axios.post('http://localhost:8000/api/delete/', {id : updatedEvent.id},{
        withCredentials: true,  // 쿠키 포함
    });
  
      // 프론트엔드 상태 업데이트
      setEventList((prevEvents) =>
        prevEvents.filter((event) => event.id !== updatedEvent.id)
    );
  
      // 모달 창 닫기
      setModalOpen(false);
    } catch (error) {
      console.error('Error updating event:', error);
      // 에러 처리 로직 (예: 사용자에게 오류 알림)
    }
  };

  return (
    <div>
      <Calendar
        selectable
        localizer={localizer}
        events={eventList}
        startAccessor="start"
        endAccessor="end"
        style={{ height: 550, width:1100}}
        onSelectEvent={handleSelectEvent}
        onSelectSlot={handleSelectSlot}
        messages={{
          next: '다음',
          previous: '이전',
          today: '오늘',
          month: '월',
          week: '주',
          day: '일',
          agenda: '일정',
        }}
      />
      {isModalOpen && (
        <Modal
          event={selectedEvent}
          slot = {selectedSlot}
          onClose={() => setModalOpen(false)}
          onSave={handleEventUpdate} // 수정 후 저장
          onDelete={handleEventDelete}
        />
      )}
    </div>
  );
}

export default MyCalendar;