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
                echo Version %APP_VERSION% is valid.
                '''
            }
        }

        stage('Unit/Application Test') {
            steps {
                echo '=== APPLICATION TEST ==='

                bat '''
                python -m py_compile app.py
                echo Application syntax test PASSED.
                '''
            }
        }

        stage('Docker Build') {
            steps {
                echo '=== DOCKER BUILD ==='

                bat '''
                docker build --build-arg APP_VERSION=%APP_VERSION% -t %APP_NAME%:%APP_VERSION% .
                '''
            }
        }

        stage('Docker Image Validation') {
            steps {
                echo '=== IMAGE VALIDATION ==='

                bat '''
                docker image inspect %APP_NAME%:%APP_VERSION% >nul 2>&1
                if errorlevel 1 exit /b 1

                echo Docker image %APP_NAME%:%APP_VERSION% exists.
                docker image inspect %APP_NAME%:%APP_VERSION% --format="{{.Id}}"
                '''
            }
        }

        stage('Start Candidate') {
            steps {
                echo '=== START GREEN CANDIDATE ==='
                echo "GREEN container: %CANDIDATE_CONTAINER%"
                echo "GREEN port: %CANDIDATE_PORT%"

                bat '''
                docker rm -f %CANDIDATE_CONTAINER% >nul 2>&1 || exit /b 0

                docker run -d ^
                --name %CANDIDATE_CONTAINER% ^
                --network %NETWORK% ^
                -p %CANDIDATE_PORT%:%CONTAINER_PORT% ^
                -e APP_VERSION=%APP_VERSION% ^
                -e ENVIRONMENT=PRODUCTION ^
                %APP_NAME%:%APP_VERSION%
                '''
            }
        }

        stage('Container Validation') {
            steps {
                echo '=== CONTAINER VALIDATION ==='

                bat '''
                docker ps --filter "name=%CANDIDATE_CONTAINER%" --filter "status=running" | findstr %CANDIDATE_CONTAINER%

                if errorlevel 1 (
                    echo Candidate container is NOT running.
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
                docker exec %CANDIDATE_CONTAINER% python -c "import socket; s=socket.create_connection(('orders-db',3306),5); print('DATABASE CONNECTION SUCCESS'); s.close()"

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
                echo 'Switching production traffic from current version to candidate.'

                bat '''
                echo Checking current production container...

                docker inspect %PROD_CONTAINER% >nul 2>&1

                if not errorlevel 1 (
                    echo Current Jenkins production container found.
                    docker stop %PROD_CONTAINER% >nul 2>&1
                    docker rm %PROD_CONTAINER% >nul 2>&1
                )

                docker inspect orders-blue-rollback >nul 2>&1

                if not errorlevel 1 (
                    echo Existing manual production container found.
                    docker stop orders-blue-rollback >nul 2>&1
                    docker rm orders-blue-rollback >nul 2>&1
                )

                echo Removing candidate temporary port mapping...

                docker stop %CANDIDATE_CONTAINER% >nul 2>&1
                docker rm %CANDIDATE_CONTAINER% >nul 2>&1

                echo Starting validated version on production port %PROD_PORT%...

                docker run -d ^
                --name %PROD_CONTAINER% ^
                --network %NETWORK% ^
                -p %PROD_PORT%:%CONTAINER_PORT% ^
                -e APP_VERSION=%APP_VERSION% ^
                -e ENVIRONMENT=PRODUCTION ^
                %APP_NAME%:%APP_VERSION%

                echo Production container started.
                '''
            }
        }

        stage('Deployment Verification') {
            steps {
                echo '=== DEPLOYMENT VERIFICATION ==='

                bat '''
                curl.exe --fail --silent --show-error http://localhost:%PROD_PORT%/health

                if errorlevel 1 (
                    echo Production verification FAILED.
                    exit /b 1
                )

                echo Production verification PASSED.

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
                docker ps --filter "name=%PROD_CONTAINER%"

                echo.
                echo ===== NETWORK =====
                docker network inspect %NETWORK%
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
        }

        failure {
            echo '=============================================='
            echo 'DEPLOYMENT FAILED'
            echo '=============================================='
            echo "Version: ${env.APP_VERSION}"
            echo "Action: ${params.ACTION}"
            echo 'Current production was not intentionally changed before candidate validation.'

            bat '''
            echo ===== CANDIDATE LOGS =====
            docker logs %CANDIDATE_CONTAINER% > candidate-failure.log 2>&1 || echo No candidate logs available.

            echo ===== CANDIDATE CLEANUP =====
            docker rm -f %CANDIDATE_CONTAINER% >nul 2>&1 || exit /b 0
            '''
        }

        always {
            echo '=============================================='
            echo 'PIPELINE EXECUTION COMPLETED'
            echo '=============================================='
        }
    }
}