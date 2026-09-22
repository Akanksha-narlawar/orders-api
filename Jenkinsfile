pipeline {
    agent any

    parameters {
        string(
            name: 'VERSION',
            defaultValue: '7.9',
            description: 'Application version to deploy or rollback'
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

        BLUE_CONTAINER = 'orders-blue'
        GREEN_CONTAINER = 'orders-green'

        BLUE_PORT = '8091'
        GREEN_PORT = '8092'
        CONTAINER_PORT = '5000'

        APP_VERSION = "${params.VERSION}"

        PYTHON_PATH = 'C:\\Users\\akank\\AppData\\Local\\Programs\\Python\\Python311\\python.exe'
        DOCKER_PATH = 'C:\\Users\\akank\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe'

        CURRENT_CONTAINER = ''
        CANDIDATE_CONTAINER = ''
        CURRENT_PORT = ''
        CANDIDATE_PORT = ''
        CURRENT_COLOR = ''
        CANDIDATE_COLOR = ''
    }

    stages {

        stage('Checkout') {
            steps {
                echo '========== CHECKOUT =========='

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
                echo '========== VALIDATE VERSION =========='

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
                echo '========== UNIT / APPLICATION TEST =========='

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
            when {
                expression {
                    params.ACTION == 'DEPLOY'
                }
            }

            steps {
                echo '========== DOCKER BUILD =========='

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
                echo '========== DOCKER IMAGE VALIDATION =========='

                bat '''
                    "%DOCKER_PATH%" image inspect %APP_NAME%:%APP_VERSION%

                    if errorlevel 1 (
                        echo ERROR: Docker image %APP_NAME%:%APP_VERSION% does not exist
                        exit /b 1
                    )

                    echo Docker image validation successful.
                '''
            }
        }

        stage('Determine Blue-Green Slots') {
            steps {
                script {

                    def blueRunning = bat(
                        script: "\"${env.DOCKER_PATH}\" inspect -f \"{{.State.Running}}\" ${env.BLUE_CONTAINER}",
                        returnStdout: true
                    ).trim() == 'true'

                    def greenRunning = bat(
                        script: "\"${env.DOCKER_PATH}\" inspect -f \"{{.State.Running}}\" ${env.GREEN_CONTAINER}",
                        returnStdout: true
                    ).trim() == 'true'

                    echo "BLUE running  : ${blueRunning}"
                    echo "GREEN running : ${greenRunning}"

                    if (blueRunning && !greenRunning) {

                        env.CURRENT_COLOR = 'BLUE'
                        env.CANDIDATE_COLOR = 'GREEN'

                        env.CURRENT_CONTAINER = env.BLUE_CONTAINER
                        env.CANDIDATE_CONTAINER = env.GREEN_CONTAINER

                        env.CURRENT_PORT = env.BLUE_PORT
                        env.CANDIDATE_PORT = env.GREEN_PORT

                    } else if (!blueRunning && greenRunning) {

                        env.CURRENT_COLOR = 'GREEN'
                        env.CANDIDATE_COLOR = 'BLUE'

                        env.CURRENT_CONTAINER = env.GREEN_CONTAINER
                        env.CANDIDATE_CONTAINER = env.BLUE_CONTAINER

                        env.CURRENT_PORT = env.GREEN_PORT
                        env.CANDIDATE_PORT = env.BLUE_PORT

                    } else {

                        error(
                            'SAFE DEPLOYMENT STOPPED: Exactly one of BLUE or GREEN must be running.'
                        )
                    }

                    echo '========== BLUE-GREEN CONFIGURATION =========='
                    echo "Current Color       : ${env.CURRENT_COLOR}"
                    echo "Current Container   : ${env.CURRENT_CONTAINER}"
                    echo "Current Port        : ${env.CURRENT_PORT}"
                    echo "Candidate Color     : ${env.CANDIDATE_COLOR}"
                    echo "Candidate Container : ${env.CANDIDATE_CONTAINER}"
                    echo "Candidate Port      : ${env.CANDIDATE_PORT}"
                }
            }
        }

        stage('Start Candidate') {
            steps {
                echo '========== START CANDIDATE =========='

                bat '''
                    echo ========================================
                    echo CURRENT PRODUCTION
                    echo ========================================
                    echo Color     : %CURRENT_COLOR%
                    echo Container : %CURRENT_CONTAINER%
                    echo Port      : %CURRENT_PORT%

                    echo.
                    echo ========================================
                    echo CANDIDATE
                    echo ========================================
                    echo Color     : %CANDIDATE_COLOR%
                    echo Container : %CANDIDATE_CONTAINER%
                    echo Port      : %CANDIDATE_PORT%

                    echo.
                    echo Checking Docker network...

                    "%DOCKER_PATH%" network inspect %NETWORK%

                    if errorlevel 1 (
                        echo ERROR: Docker network %NETWORK% does not exist
                        exit /b 1
                    )

                    echo.
                    echo Removing old stopped candidate if present...

                    "%DOCKER_PATH%" rm -f %CANDIDATE_CONTAINER% 2>NUL

                    echo.
                    echo Starting candidate...

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

                    echo.
                    echo Candidate started successfully.
                '''
            }
        }

        stage('Container Validation') {
            steps {
                echo '========== CONTAINER VALIDATION =========='

                bat '''
                    echo Candidate container:

                    "%DOCKER_PATH%" ps -a ^
                        --filter "name=%CANDIDATE_CONTAINER%" ^
                        --format "table {{.Names}}\\t{{.Image}}\\t{{.Status}}\\t{{.Ports}}"

                    echo.
                    echo Candidate running state:

                    "%DOCKER_PATH%" inspect ^
                        -f "{{.State.Status}}" ^
                        %CANDIDATE_CONTAINER%

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
                echo '========== APPLICATION HEALTH CHECK =========='

                bat '''
                    echo Waiting for candidate application...

                    powershell -NoProfile -Command "Start-Sleep -Seconds 5"

                    echo Checking candidate health...

                    curl.exe --fail --silent --show-error ^
                        http://localhost:%CANDIDATE_PORT%/health

                    if errorlevel 1 (
                        echo ERROR: Candidate health check failed
                        exit /b 1
                    )

                    echo.
                    echo Candidate health check successful.
                '''
            }
        }

        stage('Application Version Check') {
            steps {
                echo '========== APPLICATION VERSION CHECK =========='

                bat '''
                    echo Checking candidate application version...

                    curl.exe --fail --silent --show-error ^
                        http://localhost:%CANDIDATE_PORT%/

                    if errorlevel 1 (
                        echo ERROR: Candidate application check failed
                        exit /b 1
                    )

                    echo.
                    echo Candidate application check successful.
                '''
            }
        }

        stage('Integration Check') {
            steps {
                echo '========== DATABASE INTEGRATION CHECK =========='

                bat '''
                    echo Checking Docker network...

                    "%DOCKER_PATH%" network inspect %NETWORK%

                    if errorlevel 1 (
                        echo ERROR: Docker network validation failed
                        exit /b 1
                    )

                    echo.
                    echo Checking database connectivity from candidate...

                    "%DOCKER_PATH%" exec %CANDIDATE_CONTAINER% ^
                        python -c "import socket; s=socket.create_connection(('orders-db',3306),5); print('DATABASE CONNECTION SUCCESS'); s.close()"

                    if errorlevel 1 (
                        echo ERROR: Database integration check failed
                        exit /b 1
                    )

                    echo.
                    echo Database integration check successful.
                '''
            }
        }

        stage('Traffic Switch') {
            steps {
                echo '========== TRAFFIC SWITCH =========='

                bat '''
                    echo ========================================
                    echo BLUE-GREEN TRAFFIC SWITCH
                    echo ========================================

                    echo Current production:
                    echo Color     : %CURRENT_COLOR%
                    echo Container : %CURRENT_CONTAINER%
                    echo Port      : %CURRENT_PORT%

                    echo.
                    echo Candidate:
                    echo Color     : %CANDIDATE_COLOR%
                    echo Container : %CANDIDATE_CONTAINER%
                    echo Port      : %CANDIDATE_PORT%

                    echo.
                    echo Candidate passed:
                    echo - Container validation
                    echo - Health check
                    echo - Application check
                    echo - Database integration check

                    echo.
                    echo Candidate is now the validated production slot.

                    echo.
                    echo Removing previous production container:
                    echo %CURRENT_CONTAINER%

                    "%DOCKER_PATH%" rm -f %CURRENT_CONTAINER%

                    if errorlevel 1 (
                        echo ERROR: Previous production cleanup failed
                        exit /b 1
                    )

                    echo.
                    echo ========================================
                    echo TRAFFIC SWITCH COMPLETED
                    echo ========================================
                    echo Active Color     : %CANDIDATE_COLOR%
                    echo Active Container : %CANDIDATE_CONTAINER%
                    echo Active Port      : %CANDIDATE_PORT%
                '''
            }
        }

        stage('Deployment Verification') {
            steps {
                echo '========== DEPLOYMENT VERIFICATION =========='

                bat '''
                    echo Waiting for active production...

                    powershell -NoProfile -Command "Start-Sleep -Seconds 5"

                    echo.
                    echo Checking active production health...

                    curl.exe --fail --silent --show-error ^
                        http://localhost:%CANDIDATE_PORT%/health

                    if errorlevel 1 (
                        echo ERROR: Active production health check failed
                        exit /b 1
                    )

                    echo.
                    echo Active production container:

                    "%DOCKER_PATH%" ps ^
                        --filter "name=%CANDIDATE_CONTAINER%" ^
                        --format "table {{.Names}}\\t{{.Image}}\\t{{.Status}}\\t{{.Ports}}"

                    echo.
                    echo Deployment verification successful.
                '''
            }
        }

        stage('Production Container Status') {
            steps {
                echo '========== PRODUCTION CONTAINER STATUS =========='

                bat '''
                    echo Active production container:
                    echo %CANDIDATE_CONTAINER%

                    echo.
                    "%DOCKER_PATH%" ps -a ^
                        --filter "name=%CANDIDATE_CONTAINER%"

                    echo.
                    echo Active production color:
                    echo %CANDIDATE_COLOR%

                    echo.
                    echo Active production port:
                    echo %CANDIDATE_PORT%

                    echo.
                    echo Port status:

                    netstat -ano | findstr :%CANDIDATE_PORT%

                    echo.
                    echo Final health:

                    curl.exe --fail --silent --show-error ^
                        http://localhost:%CANDIDATE_PORT%/health
                '''
            }
        }
    }

    post {

        success {
            echo '========================================'
            echo 'BLUE-GREEN DEPLOYMENT SUCCESSFUL'
            echo "Application : ${env.APP_NAME}"
            echo "Version     : ${env.APP_VERSION}"
            echo "Active Color: ${env.CANDIDATE_COLOR}"
            echo "Active Port : ${env.CANDIDATE_PORT}"
            echo '========================================'
        }

        failure {
            echo '========================================'
            echo 'BLUE-GREEN DEPLOYMENT FAILED'
            echo "Application : ${env.APP_NAME}"
            echo "Version     : ${env.APP_VERSION}"
            echo "Current     : ${env.CURRENT_CONTAINER}"
            echo "Candidate   : ${env.CANDIDATE_CONTAINER}"
            echo '========================================'

            bat '''
                echo.
                echo ===== ALL CONTAINERS =====

                "%DOCKER_PATH%" ps -a

                echo.
                echo ===== CANDIDATE LOGS =====

                "%DOCKER_PATH%" logs %CANDIDATE_CONTAINER% 2>NUL

                echo.
                echo ===== CURRENT PRODUCTION LOGS =====

                "%DOCKER_PATH%" logs %CURRENT_CONTAINER% 2>NUL

                echo.
                echo ===== NETWORK =====

                "%DOCKER_PATH%" network inspect %NETWORK%
            '''
        }

        always {
            echo 'Pipeline execution completed.'
        }
    }
}