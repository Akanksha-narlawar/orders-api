pipeline {
    agent any

    parameters {
        string(
            name: 'VERSION',
            defaultValue: '7.9',
            description: 'Application version to deploy'
        )

        choice(
            name: 'ACTION',
            choices: ['DEPLOY', 'ROLLBACK'],
            description: 'Deployment action'
        )
    }

    environment {
        APP_NAME = 'orders-api'
        NETWORK = 'orders-network'
        DB_CONTAINER = 'orders-db'

        CANDIDATE_CONTAINER = 'orders-green-jenkins'
        PROD_CONTAINER = 'orders-prod-jenkins'

        CANDIDATE_PORT = '8085'
        PROD_PORT = '8087'
        CONTAINER_PORT = '5000'

        APP_VERSION = "${params.VERSION}"

        PYTHON_PATH = 'C:\\Users\\akank\\AppData\\Local\\Programs\\Python\\Python311\\python.exe'
        DOCKER_PATH = 'C:\\Users\\akank\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe'
    }

    stages {

        stage('Checkout') {
            steps {
                echo "========== CHECKOUT =========="

                checkout scm

                bat '''
                    "%DOCKER_PATH%" --version
                    git rev-parse HEAD
                    git status
                '''
            }
        }

        stage('Validate Version') {
            steps {
                echo "========== VALIDATE VERSION =========="

                bat '''
                    echo Application Version: %APP_VERSION%

                    if "%APP_VERSION%"=="" (
                        echo ERROR: VERSION parameter is empty
                        exit /b 1
                    )

                    echo Version validation successful.
                '''
            }
        }

        stage('Unit/Application Test') {
            steps {
                echo "========== UNIT / APPLICATION TEST =========="

                bat '''
                    "%PYTHON_PATH%" -m py_compile app.py

                    if errorlevel 1 (
                        echo ERROR: Python compilation failed
                        exit /b 1
                    )

                    echo Python application test successful.
                '''
            }
        }

        stage('Docker Build') {
            steps {
                echo "========== DOCKER BUILD =========="

                bat '''
                    "%DOCKER_PATH%" build ^
                        --build-arg APP_VERSION=%APP_VERSION% ^
                        -t %APP_NAME%:%APP_VERSION% .

                    if errorlevel 1 (
                        echo ERROR: Docker image build failed
                        exit /b 1
                    )

                    echo Docker image build successful.
                '''
            }
        }

        stage('Docker Image Validation') {
            steps {
                echo "========== DOCKER IMAGE VALIDATION =========="

                bat '''
                    "%DOCKER_PATH%" image inspect %APP_NAME%:%APP_VERSION%

                    if errorlevel 1 (
                        echo ERROR: Docker image does not exist
                        exit /b 1
                    )

                    echo Docker image validation successful.
                '''
            }
        }

        stage('Start Candidate') {
            steps {
                echo "========== START CANDIDATE =========="

                bat '''
                    echo Removing old candidate container if present...

                    "%DOCKER_PATH%" rm -f %CANDIDATE_CONTAINER% 2>NUL

                    echo Checking Docker network...

                    "%DOCKER_PATH%" network inspect %NETWORK%

                    if errorlevel 1 (
                        echo ERROR: Docker network %NETWORK% does not exist
                        exit /b 1
                    )

                    echo Starting candidate container...

                    "%DOCKER_PATH%" run -d ^
                        --name %CANDIDATE_CONTAINER% ^
                        --network %NETWORK% ^
                        -p %CANDIDATE_PORT%:%CONTAINER_PORT% ^
                        -e APP_VERSION=%APP_VERSION% ^
                        -e ENVIRONMENT=PRODUCTION ^
                        %APP_NAME%:%APP_VERSION%

                    if errorlevel 1 (
                        echo ERROR: Candidate container failed to start
                        exit /b 1
                    )

                    echo Candidate container started successfully.
                '''
            }
        }

        stage('Container Validation') {
            steps {
                echo "========== CONTAINER VALIDATION =========="

                bat '''
                    "%DOCKER_PATH%" ps -a --filter "name=%CANDIDATE_CONTAINER%"

                    "%DOCKER_PATH%" inspect %CANDIDATE_CONTAINER%

                    if errorlevel 1 (
                        echo ERROR: Candidate container validation failed
                        exit /b 1
                    )

                    echo Candidate container validation successful.
                '''
            }
        }

        stage('Application Health Check') {
            steps {
                echo "========== APPLICATION HEALTH CHECK =========="

                bat '''
                    echo Waiting for application...

                    timeout /t 5 /nobreak

                    echo Checking application health...

                    curl.exe --fail --silent --show-error ^
                        http://localhost:%CANDIDATE_PORT%/health

                    if errorlevel 1 (
                        echo ERROR: Candidate health check failed
                        exit /b 1
                    )

                    echo Candidate health check successful.
                '''
            }
        }

        stage('Integration Check') {
            steps {
                echo "========== DATABASE INTEGRATION CHECK =========="

                bat '''
                    echo Checking Docker network...

                    "%DOCKER_PATH%" network inspect %NETWORK%

                    echo Checking database connectivity from candidate...

                    "%DOCKER_PATH%" exec %CANDIDATE_CONTAINER% ^
                    python -c "import socket; s=socket.create_connection(('orders-db',3306),5); print('DATABASE CONNECTION SUCCESS'); s.close()"

                    if errorlevel 1 (
                        echo ERROR: Database integration check failed
                        exit /b 1
                    )

                    echo Database integration check successful.
                '''
            }
        }

        stage('Traffic Switch') {
            steps {
                echo "========== TRAFFIC SWITCH =========="

                bat '''
                    echo Current Docker containers:

                    "%DOCKER_PATH%" ps --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}"

                    echo.
                    echo Current production port:
                    echo %PROD_PORT%

                    echo.
                    echo Stopping existing production container if present...

                    "%DOCKER_PATH%" rm -f %PROD_CONTAINER% 2>NUL

                    echo.
                    echo Starting new production container...

                    "%DOCKER_PATH%" run -d ^
                        --name %PROD_CONTAINER% ^
                        --network %NETWORK% ^
                        -p %PROD_PORT%:%CONTAINER_PORT% ^
                        -e APP_VERSION=%APP_VERSION% ^
                        -e ENVIRONMENT=PRODUCTION ^
                        %APP_NAME%:%APP_VERSION%

                    if errorlevel 1 (
                        echo ERROR: Traffic switch failed
                        exit /b 1
                    )

                    echo Traffic switch successful.
                '''
            }
        }

        stage('Deployment Verification') {
            steps {
                echo "========== DEPLOYMENT VERIFICATION =========="

                bat '''
                    echo Waiting for production application...

                    timeout /t 5 /nobreak

                    echo Checking production health...

                    curl.exe --fail --silent --show-error ^
                        http://localhost:%PROD_PORT%/health

                    if errorlevel 1 (
                        echo ERROR: Production health check failed
                        exit /b 1
                    )

                    echo.
                    echo Checking production container...

                    "%DOCKER_PATH%" ps --filter "name=%PROD_CONTAINER%"

                    echo.
                    echo Deployment verification successful.
                '''
            }
        }

        stage('Production Container Status') {
            steps {
                echo "========== PRODUCTION CONTAINER STATUS =========="

                bat '''
                    "%DOCKER_PATH%" ps -a --filter "name=%PROD_CONTAINER%"

                    echo.
                    echo Production port:

                    netstat -ano | findstr :%PROD_PORT%

                    echo.
                    echo Production health:

                    curl.exe --fail --silent --show-error ^
                        http://localhost:%PROD_PORT%/health
                '''
            }
        }
    }

    post {

        success {
            echo "========================================"
            echo "DEPLOYMENT SUCCESSFUL"
            echo "Application : %APP_NAME%"
            echo "Version     : %APP_VERSION%"
            echo "Port        : %PROD_PORT%"
            echo "========================================"
        }

        failure {
            echo "========================================"
            echo "DEPLOYMENT FAILED"
            echo "Application : %APP_NAME%"
            echo "Version     : %APP_VERSION%"
            echo "========================================"

            bat '''
                echo.
                echo ===== ALL CONTAINERS =====

                "%DOCKER_PATH%" ps -a

                echo.
                echo ===== CANDIDATE LOGS =====

                "%DOCKER_PATH%" logs %CANDIDATE_CONTAINER% 2>NUL

                echo.
                echo ===== PRODUCTION LOGS =====

                "%DOCKER_PATH%" logs %PROD_CONTAINER% 2>NUL

                echo.
                echo ===== NETWORK =====

                "%DOCKER_PATH%" network inspect %NETWORK%
            '''
        }

        always {
            echo "Pipeline execution completed."

            archiveArtifacts artifacts: 'candidate-failure.log',
                             allowEmptyArchive: true
        }
    }
}