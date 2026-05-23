@echo off
echo ====================================
echo  Tour Guide Application - Starting
echo ====================================

:: Set JAVA_HOME automatically (IntelliJ JDK)
set JAVA_HOME=C:\Users\ASUS\.jdks\ms-21.0.7
set PATH=%JAVA_HOME%\bin;%PATH%

echo.
echo [1/3] Starting Spring Boot Backend (with H2 Database)...
cd Tour-Guide-booking
start "Spring Boot Backend" cmd /k "set JAVA_HOME=C:\Users\ASUS\.jdks\ms-21.0.7 && set PATH=%JAVA_HOME%\bin;%PATH% && mvnw.cmd spring-boot:run"
cd ..

echo.
echo [2/3] Starting AI Python Service...
cd ai-service
start "AI Python Service" cmd /k "python app.py"
cd ..

echo.
echo [3/3] Starting React Frontend...
cd Tour-Guide-booking\frontend
start "React Frontend" cmd /k "npm install --legacy-peer-deps && npm run dev"
cd ..\..

echo.
echo ====================================
echo  All services starting up!
echo ====================================
echo  Backend  : http://localhost:8080
echo  AI Service: http://localhost:5000
echo  Frontend : http://localhost:5173
echo  DB Console: http://localhost:8080/h2-console
echo.
echo  Admin Login:
echo  Email   : admin@tourguide.com
echo  Password: admin123
echo ====================================
echo.
pause
