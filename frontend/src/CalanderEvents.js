import React, { useEffect, useState } from 'react';
import axios from 'axios';
import MyCalendar from './Calander';

function CalendarAuth() {
    const [events, setEvents] = useState([]);
    const [loading, setLoading] = useState(true);
  
    useEffect(() => {
      axios.get('http://localhost:8000/api/events/', { withCredentials: true })
        .then(response => {
          setEvents(response.data);
          setLoading(false);
        })
        .catch(error => {
          console.error('이벤트를 가져오는 중 오류 발생:', error);
          setLoading(false);
        });
    }, []);
  
    if (loading) {
      return <div>로딩 중...</div>;
    }
  
    if (!events || events.length === 0) {
      return <div>이벤트가 없습니다.</div>;
    }
  
    return (
      <div>
        <MyCalendar eventDataArray={events} />
      </div>
    );
  }
  
  export default CalendarAuth;