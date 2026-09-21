pipeline {
    agent any

    parameters {
        string(name: 'VERSION', defaultValue: '7.9', description: 'Application version')
        choice(name: 'ACTION', choices: ['DEPLOY', 'ROLLBACK'], description: 'Deployment action')
    }

    environment {
        APP_NAME = 'orders-api'
        NETWORK = 'orders-network'
        DB_CONTAINER = 'orders-db'
        CANDIDATE_CONTAINER = 'orders-green-jenkins'
        PROD_PORT = '8082'
        CONTAINER_PORT = '5000'
    }

    stages {

        stage('Checkout') {
            steps {
                echo '=== CHECKOUT ==='
                checkout scm
            }
        }

        stage('Validate Version') {
            steps {
                echo "=== VALIDATE VERSION ==="
                bat "docker image inspect %APP_NAME%:%VERSION% >nul 2>&1 || exit /b 1"
                echo "Docker image %APP_NAME%:%VERSION% exists."
            }
        }

        stage('Unit/Application Test') {
            steps {
                echo '=== APPLICATION TEST ==='
                bat 'python -m py_compile app.py'
            }
        }

        stage('Docker Build') {
            steps {
                echo '=== DOCKER BUILD ==='
                bat "docker build --build-arg APP_VERSION=%VERSION% -t %APP_NAME%:%VERSION% ."
            }
        }

        stage('Docker Image Validation') {
            steps {
                echo '=== IMAGE VALIDATION ==='
                bat "docker image inspect %APP_NAME%:%VERSION%"
            }
        }

        stage('Start Candidate') {
            steps {
                echo '=== START CANDIDATE ==='

                bat '''
                docker rm -f %CANDIDATE_CONTAINER% >nul 2>&1 || exit /b 0
                docker run -d --name %CANDIDATE_CONTAINER% --network %NETWORK% -p 8085:%CONTAINER_PORT% -e APP_VERSION=%VERSION% -e ENVIRONMENT=PRODUCTION %APP_NAME%:%VERSION%
                '''
            }
        }

        stage('Container Validation') {
            steps {
                echo '=== CONTAINER VALIDATION ==='

                bat '''
                docker ps --filter "name=%CANDIDATE_CONTAINER%" --filter "status=running" | findstr %CANDIDATE_CONTAINER%
                if errorlevel 1 exit /b 1
                '''
            }
        }

        stage('Application Health Check') {
            steps {
                echo '=== HEALTH CHECK ==='

                bat '''
                curl.exe --fail --silent --show-error http://localhost:8085/health
                '''
            }
        }

        stage('Integration Check') {
            steps {
                echo '=== DATABASE INTEGRATION CHECK ==='

                bat '''
                docker exec %CANDIDATE_CONTAINER% python -c "import socket; s=socket.create_connection(('orders-db',3306),5); print('DATABASE CONNECTION SUCCESS'); s.close()"
                '''
            }
        }

        stage('Traffic Switch') {
            when {
                expression {
                    params.ACTION == 'DEPLOY'
                }
            }

            steps {
                echo '=== TRAFFIC SWITCH ==='

                bat '''
                docker rm -f orders-blue-rollback >nul 2>&1 || exit /b 0
                docker rm -f orders-green >nul 2>&1 || exit /b 0

                docker rename %CANDIDATE_CONTAINER% orders-green

                docker stop orders-blue >nul 2>&1 || exit /b 0
                '''
            }
        }

        stage('Old Version Cleanup') {
            when {
                expression {
                    params.ACTION == 'DEPLOY'
                }
            }

            steps {
                echo '=== OLD VERSION CLEANUP ==='

                bat '''
                docker rm orders-blue >nul 2>&1 || exit /b 0
                '''
            }
        }

        stage('Deployment Verification') {
            steps {
                echo '=== DEPLOYMENT VERIFICATION ==='

                bat '''
                curl.exe --fail --silent --show-error http://localhost:8085/health
                '''
            }
        }
    }

    post {
        success {
            echo '===================================='
            echo 'DEPLOYMENT SUCCESSFUL'
            echo '===================================='
        }

        failure {
            echo '===================================='
            echo 'DEPLOYMENT FAILED'
            echo 'Candidate will not be promoted.'
            echo '===================================='

            bat '''
            docker logs %CANDIDATE_CONTAINER% > candidate-failure.log 2>&1
            docker rm -f %CANDIDATE_CONTAINER% >nul 2>&1 || exit /b 0
            '''
        }

        always {
            echo 'Pipeline execution completed.'
        }
    }
}