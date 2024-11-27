import "./loginPage.css"
function LoginPage(){
    const handleGoogleLogin = () => {
        window.location.href = 'http://localhost:8000/api/calendar/init/';
      };
    return(
        <div className="login-page">
            <div className="page-title">썸데이</div>
            <div className="center-box">
                <div className = "info-part">썸데이를 사용하기 위해 로그인을 해주세요</div>
                <button className = "login-button" onClick={handleGoogleLogin}>로그인</button>
            </div>
        </div>
    )
}
export default LoginPage;