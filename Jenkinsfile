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

        PYTHON_PATH = 'C:\\Users\\akank\\AppData\\Local\\Programs\\Python\\Python311\\python.exe'
        DOCKER_PATH = 'C:\\Program Files\\Docker\\Docker\\resources\\bin\\docker.exe'
    }

    stages {

        stage('Checkout') {
            steps {
                echo '=== CHECKOUT ==='
                echo "Git commit: ${env.GIT_COMMIT}"
                checkout scm
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
                "%DOCKER_PATH%" build --build-arg APP_VERSION=%APP_VERSION% -t %APP_NAME%:%APP_VERSION% .

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

                "%DOCKER_PATH%" image inspect %APP_NAME%:%APP_VERSION% --format="{{.Id}}"
                '''
            }
        }

        stage('Start Candidate') {
            steps {
                echo '=== START GREEN CANDIDATE ==='
                echo "GREEN container: %CANDIDATE_CONTAINER%"
                echo "GREEN port: %CANDIDATE_PORT%"

                bat '''
                "%DOCKER_PATH%" rm -f %CANDIDATE_CONTAINER% >nul 2>&1

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
                "%DOCKER_PATH%" ps --filter "name=%CANDIDATE_CONTAINER%" --filter "status=running" | findstr %CANDIDATE_CONTAINER%

                if errorlevel 1 (
                    echo Candidate container is NOT running.
                    "%DOCKER_PATH%" ps -a --filter "name=%CANDIDATE_CONTAINER%"
                    exit /b 1
                )

                echo Candidate container is RUNNING.
                '''
            }
        }

        stage('Application Health Check') {
            steps {
                echo '=== APPLICATION HEALTH CHECK ==='

                bat '''
                curl.exe --fail --silent --show-error http://localhost:%CANDIDATE_PORT%/health

                if errorlevel 1 (
                    echo Candidate health check FAILED.
                    exit /b 1
                )

                echo Candidate health check PASSED.
                '''
            }
        }

        stage('Integration Check') {
            steps {
                echo '=== DATABASE INTEGRATION CHECK ==='

                bat '''
                "%DOCKER_PATH%" exec %CANDIDATE_CONTAINER% "%PYTHON_PATH%" -c "import socket; s=socket.create_connection(('orders-db',3306),5); print('DATABASE CONNECTION SUCCESS'); s.close()"

                if errorlevel 1 (
                    echo Database integration FAILED.
                    exit /b 1
                )

                echo Database integration PASSED.
                '''
            }
        }

        stage('Traffic Switch') {
            when {
                expression {
                    params.ACTION == 'DEPLOY' || params.ACTION == 'ROLLBACK'
                }
            }

            steps {
                echo '=== TRAFFIC SWITCH ==='
                echo 'GREEN candidate passed all validation.'
                echo 'Switching production to validated version.'

                bat '''
                echo.
                echo ===== CURRENT PRODUCTION =====

                "%DOCKER_PATH%" ps --filter "name=%PROD_CONTAINER%"

                echo.
                echo ===== STOP OLD PRODUCTION =====

                "%DOCKER_PATH%" inspect %PROD_CONTAINER% >nul 2>&1

                if not errorlevel 1 (
                    echo Existing Jenkins production found.
                    "%DOCKER_PATH%" stop %PROD_CONTAINER%
                    "%DOCKER_PATH%" rm %PROD_CONTAINER%
                )

                "%DOCKER_PATH%" inspect orders-blue-rollback >nul 2>&1

                if not errorlevel 1 (
                    echo Existing manual production found.
                    "%DOCKER_PATH%" stop orders-blue-rollback
                    "%DOCKER_PATH%" rm orders-blue-rollback
                )

                echo.
                echo ===== REMOVE TEMPORARY GREEN CONTAINER =====

                "%DOCKER_PATH%" stop %CANDIDATE_CONTAINER%
                "%DOCKER_PATH%" rm %CANDIDATE_CONTAINER%

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

                echo.
                echo Production traffic switched successfully.
                echo Active version: %APP_VERSION%
                echo Production port: %PROD_PORT%
                '''
            }
        }

        stage('Deployment Verification') {
            steps {
                echo '=== DEPLOYMENT VERIFICATION ==='

                bat '''
                curl.exe --fail --silent --show-error http://localhost:%PROD_PORT%/health

                if errorlevel 1 (
                    echo Production health verification FAILED.
                    exit /b 1
                )

                echo Production health verification PASSED.

                echo.
                echo ===== CURRENT PRODUCTION =====

                curl.exe http://localhost:%PROD_PORT%/

                echo.
                '''
            }
        }

        stage('Production Container Status') {
            steps {
                echo '=== PRODUCTION CONTAINER STATUS ==='

                bat '''
                echo.
                echo ===== PRODUCTION CONTAINER =====
                "%DOCKER_PATH%" ps --filter "name=%PROD_CONTAINER%"

                echo.
                echo ===== DOCKER NETWORK =====
                "%DOCKER_PATH%" network inspect %NETWORK%

                echo.
                echo ===== DATABASE =====
                "%DOCKER_PATH%" ps --filter "name=%DB_CONTAINER%"
                '''
            }
        }
    }

    post {

        success {
            echo '=============================================='
            echo 'DEPLOYMENT SUCCESSFUL'
            echo '=============================================='
            echo "Application: ${env.APP_NAME}"
            echo "Version: ${env.APP_VERSION}"
            echo "Action: ${params.ACTION}"
            echo "Git Commit: ${env.GIT_COMMIT}"
            echo 'Production Port: 8082'
            echo '=============================================='
        }

        failure {
            echo '=============================================='
            echo 'DEPLOYMENT FAILED'
            echo '=============================================='
            echo "Version: ${env.APP_VERSION}"
            echo "Action: ${params.ACTION}"
            echo 'Candidate will be cleaned up.'
            echo '=============================================='

            bat '''
            echo ===== CANDIDATE LOGS =====

            "%DOCKER_PATH%" logs %CANDIDATE_CONTAINER% > candidate-failure.log 2>&1

            if errorlevel 1 (
                echo No candidate logs available.
            )

            echo.
            echo ===== CANDIDATE CLEANUP =====

            "%DOCKER_PATH%" rm -f %CANDIDATE_CONTAINER% >nul 2>&1

            echo Candidate cleanup completed.
            '''
        }

        always {
            echo '=============================================='
            echo 'PIPELINE EXECUTION COMPLETED'
            echo '=============================================='
        }
    }
}