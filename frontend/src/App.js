import logo from './logo.svg';
import './App.css';
import {Routes,Route, BrowserRouter} from 'react-router-dom';
import Homepage from './Homepage';
import CalendarAuth from './CalanderEvents';
import LoginPage from './loginPage';
import PlaceList from './PlaceList';
import MakeSchedule from './MakeSchedule';
import ResultPage from './ResultPage';

function App() {
  return (
    <div>
      <BrowserRouter>
        <Routes>
          <Route path='/' element = {<LoginPage/>}></Route>
          <Route path = "/home" element = {<Homepage/>}></Route>
          <Route path='/list' element = {<PlaceList/>}></Route>
          <Route path = "/make" element = {<MakeSchedule/>}></Route>
          <Route path = "/result" element = {<ResultPage/>}></Route>
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
