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

        DOCKER_PATH = 'C:\\Users\\akank\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe'
        PYTHON_PATH = 'C:\\Users\\akank\\AppData\\Local\\Programs\\Python\\Python311\\python.exe'

        NETWORK = 'orders-network'
        DB_CONTAINER = 'orders-db'

        BLUE_CONTAINER = 'orders-blue'
        GREEN_CONTAINER = 'orders-green'

        BLUE_PORT = '8091'
        GREEN_PORT = '8092'

        CURRENT_COLOR = ''
        CURRENT_CONTAINER = ''
        CURRENT_PORT = ''

        CANDIDATE_COLOR = ''
        CANDIDATE_CONTAINER = ''
        CANDIDATE_PORT = ''

        GIT_SHA = ''
    }

    stages {

        stage('Checkout') {
            steps {
                echo '========== CHECKOUT =========='

                checkout scm

                script {
                    env.GIT_SHA = bat(
                        script: '@echo off && git rev-parse HEAD',
                        returnStdout: true
                    ).trim()

                    echo "Git SHA: ${env.GIT_SHA}"
                }

                bat """
                    "${env.DOCKER_PATH}" --version
                    git status
                """
            }
        }

        stage('Validate Version') {
            steps {
                echo '========== VALIDATE VERSION =========='

                bat """
                    echo Application Version: %VERSION%

                    if "%VERSION%" == "" (
                        echo ERROR: VERSION parameter is empty
                        exit /b 1
                    )

                    echo Version validation successful.
                """
            }
        }

        stage('Unit/Application Test') {
            steps {
                echo '========== UNIT / APPLICATION TEST =========='

                bat """
                    "${env.PYTHON_PATH}" -m py_compile app.py

                    if errorlevel 1 (
                        echo ERROR: Python compilation failed
                        exit /b 1
                    )

                    echo Python application test successful.
                """
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

                bat """
                    "${env.DOCKER_PATH}" build ^
                        --build-arg APP_VERSION=%VERSION% ^
                        -t %APP_NAME%:%VERSION% .

                    if errorlevel 1 (
                        echo ERROR: Docker image build failed
                        exit /b 1
                    )

                    echo Docker image build successful.
                """
            }
        }

        stage('Docker Image Validation') {
            steps {
                echo '========== DOCKER IMAGE VALIDATION =========='

                bat """
                    "${env.DOCKER_PATH}" image inspect %APP_NAME%:%VERSION%

                    if errorlevel 1 (
                        echo ERROR: Docker image %APP_NAME%:%VERSION% does not exist
                        exit /b 1
                    )

                    echo Docker image validation successful.
                """
            }
        }

        stage('Determine Blue-Green Slots') {
            steps {
                script {
                    echo '========== DETERMINE BLUE-GREEN SLOTS =========='

                    /*
                     * IMPORTANT:
                     * A missing Docker container is NOT a pipeline failure.
                     * It simply means that slot is currently unused.
                     */

                    def blueStatus = bat(
                        script: """
                            @echo off
                            "${env.DOCKER_PATH}" inspect -f "{{.State.Running}}" ${env.BLUE_CONTAINER} >NUL 2>&1

                            if errorlevel 1 (
                                exit /b 2
                            )

                            exit /b 0
                        """,
                        returnStatus: true
                    )

                    def greenStatus = bat(
                        script: """
                            @echo off
                            "${env.DOCKER_PATH}" inspect -f "{{.State.Running}}" ${env.GREEN_CONTAINER} >NUL 2>&1

                            if errorlevel 1 (
                                exit /b 2
                            )

                            exit /b 0
                        """,
                        returnStatus: true
                    )

                    echo "BLUE inspect status  : ${blueStatus}"
                    echo "GREEN inspect status : ${greenStatus}"

                    def blueRunning = (blueStatus == 0)
                    def greenRunning = (greenStatus == 0)

                    echo "BLUE running  : ${blueRunning}"
                    echo "GREEN running : ${greenRunning}"

                    if (blueRunning && !greenRunning) {

                        env.CURRENT_COLOR = 'BLUE'
                        env.CURRENT_CONTAINER = env.BLUE_CONTAINER
                        env.CURRENT_PORT = env.BLUE_PORT

                        env.CANDIDATE_COLOR = 'GREEN'
                        env.CANDIDATE_CONTAINER = env.GREEN_CONTAINER
                        env.CANDIDATE_PORT = env.GREEN_PORT

                    } else if (greenRunning && !blueRunning) {

                        env.CURRENT_COLOR = 'GREEN'
                        env.CURRENT_CONTAINER = env.GREEN_CONTAINER
                        env.CURRENT_PORT = env.GREEN_PORT

                        env.CANDIDATE_COLOR = 'BLUE'
                        env.CANDIDATE_CONTAINER = env.BLUE_CONTAINER
                        env.CANDIDATE_PORT = env.BLUE_PORT

                    } else if (!blueRunning && !greenRunning) {

                        error('No active BLUE or GREEN container found. Deployment stopped safely.')

                    } else {

                        error('Both BLUE and GREEN containers are running. Deployment stopped safely.')
                    }

                    echo '----------------------------------------'
                    echo "Current Color      : ${env.CURRENT_COLOR}"
                    echo "Current Container  : ${env.CURRENT_CONTAINER}"
                    echo "Current Port       : ${env.CURRENT_PORT}"
                    echo "Candidate Color    : ${env.CANDIDATE_COLOR}"
                    echo "Candidate Container: ${env.CANDIDATE_CONTAINER}"
                    echo "Candidate Port     : ${env.CANDIDATE_PORT}"
                    echo '----------------------------------------'
                }
            }
        }

        stage('Start Candidate') {
            steps {
                script {
                    echo '========== START CANDIDATE =========='

                    echo "Starting ${env.CANDIDATE_COLOR}"
                    echo "Container: ${env.CANDIDATE_CONTAINER}"
                    echo "Port: ${env.CANDIDATE_PORT}"
                    echo "Version: ${params.VERSION}"

                    bat """
                        "${env.DOCKER_PATH}" rm -f ${env.CANDIDATE_CONTAINER} 2>NUL || exit /b 0

                        "${env.DOCKER_PATH}" run -d ^
                            --name ${env.CANDIDATE_CONTAINER} ^
                            --network ${env.NETWORK} ^
                            -p ${env.CANDIDATE_PORT}:5000 ^
                            -e APP_VERSION=%VERSION% ^
                            -e ENVIRONMENT=PRODUCTION ^
                            %APP_NAME%:%VERSION%

                        if errorlevel 1 (
                            echo ERROR: Candidate container failed to start
                            exit /b 1
                        )

                        echo Candidate container started successfully.
                    """

                    bat """
                        powershell -Command "Start-Sleep -Seconds 5"
                    """
                }
            }
        }

        stage('Container Validation') {
            steps {
                echo '========== CONTAINER VALIDATION =========='

                bat """
                    "${env.DOCKER_PATH}" inspect ${env.CANDIDATE_CONTAINER}

                    if errorlevel 1 (
                        echo ERROR: Candidate container does not exist
                        exit /b 1
                    )

                    "${env.DOCKER_PATH}" inspect -f "{{.State.Running}}" ${env.CANDIDATE_CONTAINER}

                    if errorlevel 1 (
                        echo ERROR: Candidate container is not running
                        exit /b 1
                    )

                    echo Candidate container validation successful.
                """
            }
        }

        stage('Application Health Check') {
            steps {
                echo '========== APPLICATION HEALTH CHECK =========='

                bat """
                    powershell -Command "try { \$r=Invoke-WebRequest -Uri 'http://localhost:%CANDIDATE_PORT%/health' -UseBasicParsing -TimeoutSec 10; Write-Host \$r.Content; if (\$r.StatusCode -ne 200) { exit 1 } } catch { Write-Host 'ERROR: Health check failed'; exit 1 }"
                """
            }
        }

        stage('Application Version Check') {
            steps {
                echo '========== APPLICATION VERSION CHECK =========='

                bat """
                    powershell -Command "try { \$r=Invoke-WebRequest -Uri 'http://localhost:%CANDIDATE_PORT%/' -UseBasicParsing -TimeoutSec 10; Write-Host \$r.Content; if (\$r.Content -notmatch '\"version\":\"%VERSION%\"') { Write-Host 'ERROR: Application version mismatch'; exit 1 } } catch { Write-Host 'ERROR: Version check failed'; exit 1 }"
                """
            }
        }

        stage('Integration Check') {
            steps {
                echo '========== DATABASE INTEGRATION CHECK =========='

                bat """
                    "${env.DOCKER_PATH}" exec ${env.CANDIDATE_CONTAINER} python -c "import socket; s=socket.create_connection(('orders-db',3306),5); print('DATABASE CONNECTION SUCCESS'); s.close()"

                    if errorlevel 1 (
                        echo ERROR: Database connectivity failed
                        exit /b 1
                    )

                    echo Database integration check successful.
                """
            }
        }

        stage('Traffic Switch') {
            steps {
                script {
                    echo '========== TRAFFIC SWITCH =========='

                    echo "Current production : ${env.CURRENT_COLOR}"
                    echo "Candidate           : ${env.CANDIDATE_COLOR}"

                    echo "Candidate passed all validations."
                    echo "Switching active production to ${env.CANDIDATE_COLOR}."

                    bat """
                        "${env.DOCKER_PATH}" stop ${env.CURRENT_CONTAINER}

                        if errorlevel 1 (
                            echo ERROR: Failed to stop current production container
                            exit /b 1
                        )

                        "${env.DOCKER_PATH}" rm ${env.CURRENT_CONTAINER}

                        if errorlevel 1 (
                            echo ERROR: Failed to remove previous production container
                            exit /b 1
                        )

                        echo Traffic switch completed successfully.
                    """
                }
            }
        }

        stage('Deployment Verification') {
            steps {
                echo '========== DEPLOYMENT VERIFICATION =========='

                bat """
                    powershell -Command "try { \$r=Invoke-WebRequest -Uri 'http://localhost:%CANDIDATE_PORT%/' -UseBasicParsing -TimeoutSec 10; Write-Host 'ACTIVE APPLICATION:'; Write-Host \$r.Content; if (\$r.StatusCode -ne 200) { exit 1 } } catch { Write-Host 'ERROR: Deployment verification failed'; exit 1 }"
                """
            }
        }

        stage('Production Container Status') {
            steps {
                echo '========== PRODUCTION CONTAINER STATUS =========='

                bat """
                    "${env.DOCKER_PATH}" ps --filter "name=%CANDIDATE_CONTAINER%"

                    echo.
                    echo Active Production:
                    echo Color: %CANDIDATE_COLOR%
                    echo Container: %CANDIDATE_CONTAINER%
                    echo Port: %CANDIDATE_PORT%
                    echo Version: %VERSION%
                """
            }
        }
    }

    post {

        success {
            echo '========================================'
            echo 'BLUE-GREEN DEPLOYMENT SUCCESSFUL'
            echo '========================================'

            echo "Application : ${env.APP_NAME}"
            echo "Version     : ${params.VERSION}"
            echo "Git SHA     : ${env.GIT_SHA}"
            echo "Active Color: ${env.CANDIDATE_COLOR}"
            echo "Container   : ${env.CANDIDATE_CONTAINER}"
            echo "Port        : ${env.CANDIDATE_PORT}"

            bat """
                echo.
                echo ===== FINAL CONTAINERS =====
                "${env.DOCKER_PATH}" ps -a --filter "name=orders"

                echo.
                echo ===== NETWORK =====
                "${env.DOCKER_PATH}" network inspect ${env.NETWORK}
            """
        }

        failure {
            echo '========================================'
            echo 'BLUE-GREEN DEPLOYMENT FAILED'
            echo '========================================'

            echo "Application : ${env.APP_NAME}"
            echo "Version     : ${params.VERSION}"
            echo "Current     : ${env.CURRENT_CONTAINER}"
            echo "Candidate   : ${env.CANDIDATE_CONTAINER}"

            bat """
                echo.
                echo ===== ALL ORDERS CONTAINERS =====
                "${env.DOCKER_PATH}" ps -a --filter "name=orders"

                echo.
                echo ===== NETWORK =====
                "${env.DOCKER_PATH}" network inspect ${env.NETWORK}

                echo.
                echo ===== CANDIDATE LOGS =====
                "${env.DOCKER_PATH}" logs ${env.CANDIDATE_CONTAINER} 2>NUL

                echo.
                echo ===== CURRENT PRODUCTION LOGS =====
                "${env.DOCKER_PATH}" logs ${env.CURRENT_CONTAINER} 2>NUL
            """
        }

        always {
            echo 'Pipeline execution completed.'
        }
    }
}