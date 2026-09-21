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
        PROD_PORT = '8082'
        CONTAINER_PORT = '5000'

        APP_VERSION = "${params.VERSION}"

        // Python on Jenkins Windows host
        PYTHON_PATH = 'C:\\Users\\akank\\AppData\\Local\\Programs\\Python\\Python311\\python.exe'

        // Docker on Jenkins Windows host
        DOCKER_PATH = 'C:\\Users\\akank\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe'
    }

    stages {

        stage('Checkout') {
            steps {
                echo '=== CHECKOUT ==='

                checkout scm

                bat '''
                echo ===== GIT COMMIT =====
                git rev-parse HEAD

                echo.
                echo ===== GIT BRANCH =====
                git branch --show-current

                echo.
                echo ===== GIT STATUS =====
                git status
                '''
            }
        }

        stage('Validate Version') {
            steps {
                echo '=== VALIDATE VERSION ==='
                echo "Requested version: ${env.APP_VERSION}"

                bat '''
                powershell -NoProfile -Command "if ('%APP_VERSION%' -notmatch '^[0-9]+\\.[0-9]+$') { Write-Host 'Invalid version format'; exit 1 }"

                if errorlevel 1 (
                    echo Version validation FAILED.
                    exit /b 1
                )

                echo Version %APP_VERSION% is valid.
                '''
            }
        }

        stage('Unit/Application Test') {
            steps {
                echo '=== APPLICATION TEST ==='

                bat '''
                echo ===== PYTHON SYNTAX CHECK =====

                "%PYTHON_PATH%" -m py_compile app.py

                if errorlevel 1 (
                    echo Application syntax test FAILED.
                    exit /b 1
                )

                echo Application syntax test PASSED.
                '''
            }
        }

        stage('Docker Build') {
            steps {
                echo '=== DOCKER BUILD ==='
                echo "Building image: %APP_NAME%:%APP_VERSION%"

                bat '''
                "%DOCKER_PATH%" build ^
                --build-arg APP_VERSION=%APP_VERSION% ^
                -t %APP_NAME%:%APP_VERSION% .

                if errorlevel 1 (
                    echo Docker build FAILED.
                    exit /b 1
                )

                echo Docker build PASSED.
                '''
            }
        }

        stage('Docker Image Validation') {
            steps {
                echo '=== IMAGE VALIDATION ==='

                bat '''
                "%DOCKER_PATH%" image inspect %APP_NAME%:%APP_VERSION% >nul 2>&1

                if errorlevel 1 (
                    echo Docker image validation FAILED.
                    exit /b 1
                )

                echo Docker image %APP_NAME%:%APP_VERSION% exists.

                echo.
                echo ===== IMAGE ID =====
                "%DOCKER_PATH%" image inspect %APP_NAME%:%APP_VERSION% --format="{{.Id}}"

                echo.
                echo ===== IMAGE CREATED =====
                "%DOCKER_PATH%" image inspect %APP_NAME%:%APP_VERSION% --format="{{.Created}}"
                '''
            }
        }

        stage('Start Candidate') {
            steps {
                echo '=== START GREEN CANDIDATE ==='
                echo "GREEN container: ${env.CANDIDATE_CONTAINER}"
                echo "GREEN port: ${env.CANDIDATE_PORT}"

                bat '''
                echo ===== REMOVE OLD GREEN CANDIDATE =====

                "%DOCKER_PATH%" rm -f %CANDIDATE_CONTAINER% >nul 2>&1

                echo.
                echo ===== VERIFY NETWORK =====

                "%DOCKER_PATH%" network inspect %NETWORK% >nul 2>&1

                if errorlevel 1 (
                    echo Docker network %NETWORK% does not exist.
                    exit /b 1
                )

                echo Network %NETWORK% exists.

                echo.
                echo ===== START GREEN CANDIDATE =====

                "%DOCKER_PATH%" run -d ^
                --name %CANDIDATE_CONTAINER% ^
                --network %NETWORK% ^
                -p %CANDIDATE_PORT%:%CONTAINER_PORT% ^
                -e APP_VERSION=%APP_VERSION% ^
                -e ENVIRONMENT=PRODUCTION ^
                %APP_NAME%:%APP_VERSION%

                if errorlevel 1 (
                    echo Failed to start GREEN candidate.
                    exit /b 1
                )

                echo GREEN candidate started successfully.
                '''
            }
        }

        stage('Container Validation') {
            steps {
                echo '=== CONTAINER VALIDATION ==='

                bat '''
                echo ===== CONTAINER STATUS =====

                "%DOCKER_PATH%" ps ^
                --filter "name=%CANDIDATE_CONTAINER%" ^
                --filter "status=running" | findstr %CANDIDATE_CONTAINER%

                if errorlevel 1 (
                    echo Candidate container is NOT running.

                    echo.
                    echo ===== CANDIDATE STATUS =====
                    "%DOCKER_PATH%" ps -a --filter "name=%CANDIDATE_CONTAINER%"

                    echo.
                    echo ===== CANDIDATE LOGS =====
                    "%DOCKER_PATH%" logs %CANDIDATE_CONTAINER%

                    exit /b 1
                )

                echo Candidate container is RUNNING.

                echo.
                echo ===== PORT MAPPING =====
                "%DOCKER_PATH%" port %CANDIDATE_CONTAINER%
                '''
            }
        }

        stage('Application Health Check') {
            steps {
                echo '=== APPLICATION HEALTH CHECK ==='

                bat '''
                echo Checking:
                echo http://localhost:%CANDIDATE_PORT%/health

                curl.exe --fail --silent --show-error ^
                http://localhost:%CANDIDATE_PORT%/health

                if errorlevel 1 (
                    echo.
                    echo Candidate health check FAILED.

                    echo.
                    echo ===== CANDIDATE LOGS =====
                    "%DOCKER_PATH%" logs %CANDIDATE_CONTAINER%

                    exit /b 1
                )

                echo.
                echo Candidate health check PASSED.
                '''
            }
        }

        stage('Integration Check') {
            steps {
                echo '=== DATABASE INTEGRATION CHECK ==='

                bat '''
                echo ===== DATABASE CONTAINER =====

                "%DOCKER_PATH%" ps ^
                --filter "name=%DB_CONTAINER%"

                echo.
                echo ===== DATABASE NETWORK =====

                "%DOCKER_PATH%" inspect %DB_CONTAINER% ^
                --format="{{json .NetworkSettings.Networks}}"

                echo.
                echo ===== TEST DATABASE CONNECTION FROM GREEN =====

                "%DOCKER_PATH%" exec %CANDIDATE_CONTAINER% ^
                python -c "import socket; s=socket.create_connection(('orders-db',3306),5); print('DATABASE CONNECTION SUCCESS'); s.close()"

                if errorlevel 1 (
                    echo.
                    echo Database integration FAILED.

                    echo.
                    echo ===== GREEN CONTAINER NETWORK =====
                    "%DOCKER_PATH%" inspect %CANDIDATE_CONTAINER% ^
                    --format="{{json .NetworkSettings.Networks}}"

                    echo.
                    echo ===== DATABASE CONTAINER STATUS =====
                    "%DOCKER_PATH%" ps -a --filter "name=%DB_CONTAINER%"

                    echo.
                    echo ===== DATABASE LOGS =====
                    "%DOCKER_PATH%" logs --tail 50 %DB_CONTAINER%

                    exit /b 1
                )

                echo.
                echo Database integration PASSED.
                '''
            }
        }

        stage('Traffic Switch') {
            steps {
                echo '=== TRAFFIC SWITCH ==='

                bat '''
                echo ===== CURRENT PRODUCTION =====

                "%DOCKER_PATH%" ps ^
                --filter "name=%PROD_CONTAINER%"

                echo.
                echo ===== STOP OLD PRODUCTION =====

                "%DOCKER_PATH%" stop %PROD_CONTAINER% >nul 2>&1
                "%DOCKER_PATH%" rm %PROD_CONTAINER% >nul 2>&1

                echo Old production removed.

                echo.
                echo ===== REMOVE GREEN CONTAINER =====

                "%DOCKER_PATH%" stop %CANDIDATE_CONTAINER% >nul 2>&1
                "%DOCKER_PATH%" rm %CANDIDATE_CONTAINER% >nul 2>&1

                echo Green candidate removed.

                echo.
                echo ===== START NEW PRODUCTION =====

                "%DOCKER_PATH%" run -d ^
                --name %PROD_CONTAINER% ^
                --network %NETWORK% ^
                -p %PROD_PORT%:%CONTAINER_PORT% ^
                -e APP_VERSION=%APP_VERSION% ^
                -e ENVIRONMENT=PRODUCTION ^
                %APP_NAME%:%APP_VERSION%

                if errorlevel 1 (
                    echo Production container failed to start.
                    exit /b 1
                )

                echo New production container started.
                '''
            }
        }

        stage('Deployment Verification') {
            steps {
                echo '=== DEPLOYMENT VERIFICATION ==='

                bat '''
                echo ===== PRODUCTION CONTAINER =====

                "%DOCKER_PATH%" ps ^
                --filter "name=%PROD_CONTAINER%" ^
                --filter "status=running" | findstr %PROD_CONTAINER%

                if errorlevel 1 (
                    echo Production container is NOT running.

                    echo.
                    echo ===== PRODUCTION STATUS =====
                    "%DOCKER_PATH%" ps -a --filter "name=%PROD_CONTAINER%"

                    echo.
                    echo ===== PRODUCTION LOGS =====
                    "%DOCKER_PATH%" logs %PROD_CONTAINER%

                    exit /b 1
                )

                echo Production container is RUNNING.

                echo.
                echo ===== PRODUCTION HEALTH =====

                curl.exe --fail --silent --show-error ^
                http://localhost:%PROD_PORT%/health

                if errorlevel 1 (
                    echo Production health check FAILED.

                    echo.
                    echo ===== PRODUCTION LOGS =====
                    "%DOCKER_PATH%" logs %PROD_CONTAINER%

                    exit /b 1
                )

                echo.
                echo Production deployment verification PASSED.
                '''
            }
        }

        stage('Production Container Status') {
            steps {
                echo '=== PRODUCTION CONTAINER STATUS ==='

                bat '''
                echo ===== DOCKER PS =====
                "%DOCKER_PATH%" ps

                echo.
                echo ===== PRODUCTION PORT =====
                "%DOCKER_PATH%" port %PROD_CONTAINER%

                echo.
                echo ===== PRODUCTION IMAGE =====
                "%DOCKER_PATH%" inspect %PROD_CONTAINER% ^
                --format="{{.Config.Image}}"

                echo.
                echo ===== PRODUCTION VERSION =====
                "%DOCKER_PATH%" inspect %PROD_CONTAINER% ^
                --format="{{range .Config.Env}}{{println .}}{{end}}" | findstr APP_VERSION
                '''
            }
        }
    }

    post {

        success {
            echo '======================================'
            echo 'DEPLOYMENT SUCCESSFUL'
            echo '======================================'
            echo "Application: ${env.APP_NAME}"
            echo "Version: ${env.APP_VERSION}"
            echo "Production container: ${env.PROD_CONTAINER}"
            echo "Production port: ${env.PROD_PORT}"
        }

        failure {
            echo '======================================'
            echo 'DEPLOYMENT FAILED'
            echo '======================================'

            bat '''
            echo ===== CANDIDATE STATUS =====
            "%DOCKER_PATH%" ps -a --filter "name=%CANDIDATE_CONTAINER%"

            echo.
            echo ===== CANDIDATE LOGS =====
            "%DOCKER_PATH%" logs --tail 100 %CANDIDATE_CONTAINER% 2>nul

            echo.
            echo ===== PRODUCTION STATUS =====
            "%DOCKER_PATH%" ps -a --filter "name=%PROD_CONTAINER%"
            '''
        }

        always {
            echo '======================================'
            echo 'FINAL DOCKER STATUS'
            echo '======================================'

            bat '''
            "%DOCKER_PATH%" ps -a
            '''
        }
    }
}