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

        BLUE_CONTAINER = 'orders-blue'
        GREEN_CONTAINER = 'orders-green'

        BLUE_PORT = '8091'
        GREEN_PORT = '8092'

        DOCKER = 'C:\\Users\\akank\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe'
        PYTHON = 'C:\\Users\\akank\\AppData\\Local\\Programs\\Python\\Python311\\python.exe'

        TRAFFIC_SWITCHED = 'false'
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
                    "${DOCKER}" --version
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
                    "${PYTHON}" -m py_compile app.py

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
                    "${DOCKER}" build ^
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
                    "${DOCKER}" image inspect %APP_NAME%:%VERSION%

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

                    def blueStatus = bat(
                        script: """
                            "${DOCKER}" inspect ${BLUE_CONTAINER} >NUL 2>NUL
                            exit /b %ERRORLEVEL%
                        """,
                        returnStatus: true
                    )

                    def greenStatus = bat(
                        script: """
                            "${DOCKER}" inspect ${GREEN_CONTAINER} >NUL 2>NUL
                            exit /b %ERRORLEVEL%
                        """,
                        returnStatus: true
                    )

                    def blueRunning = false
                    def greenRunning = false

                    if (blueStatus == 0) {
                        def result = bat(
                            script: """
                                @echo off
                                "${DOCKER}" inspect -f "{{.State.Running}}" ${BLUE_CONTAINER}
                            """,
                            returnStdout: true
                        ).trim()

                        blueRunning = result.contains('true')
                    }

                    if (greenStatus == 0) {
                        def result = bat(
                            script: """
                                @echo off
                                "${DOCKER}" inspect -f "{{.State.Running}}" ${GREEN_CONTAINER}
                            """,
                            returnStdout: true
                        ).trim()

                        greenRunning = result.contains('true')
                    }

                    echo "BLUE inspect status  : ${blueStatus}"
                    echo "GREEN inspect status : ${greenStatus}"
                    echo "BLUE running         : ${blueRunning}"
                    echo "GREEN running        : ${greenRunning}"

                    if (blueRunning && greenRunning) {
                        error('Both BLUE and GREEN containers are running. Deployment stopped safely.')
                    }

                    if (!blueRunning && !greenRunning) {
                        error('Neither BLUE nor GREEN container is running. No current production container found.')
                    }

                    if (blueRunning) {

                        env.CURRENT_COLOR = 'BLUE'
                        env.CURRENT_CONTAINER = BLUE_CONTAINER
                        env.CURRENT_PORT = BLUE_PORT

                        env.CANDIDATE_COLOR = 'GREEN'
                        env.CANDIDATE_CONTAINER = GREEN_CONTAINER
                        env.CANDIDATE_PORT = GREEN_PORT

                    } else {

                        env.CURRENT_COLOR = 'GREEN'
                        env.CURRENT_CONTAINER = GREEN_CONTAINER
                        env.CURRENT_PORT = GREEN_PORT

                        env.CANDIDATE_COLOR = 'BLUE'
                        env.CANDIDATE_CONTAINER = BLUE_CONTAINER
                        env.CANDIDATE_PORT = BLUE_PORT
                    }

                    echo '----------------------------------------'
                    echo "Current Color       : ${env.CURRENT_COLOR}"
                    echo "Current Container   : ${env.CURRENT_CONTAINER}"
                    echo "Current Port        : ${env.CURRENT_PORT}"
                    echo "Candidate Color     : ${env.CANDIDATE_COLOR}"
                    echo "Candidate Container : ${env.CANDIDATE_CONTAINER}"
                    echo "Candidate Port      : ${env.CANDIDATE_PORT}"
                    echo '----------------------------------------'
                }
            }
        }


        stage('Start Candidate') {
            steps {
                script {

                    echo '========== START CANDIDATE =========='
                    echo "Starting       : ${env.CANDIDATE_COLOR}"
                    echo "Container      : ${env.CANDIDATE_CONTAINER}"
                    echo "Port           : ${env.CANDIDATE_PORT}"
                    echo "Version        : ${params.VERSION}"

                    bat """
                        "${DOCKER}" rm -f ${CANDIDATE_CONTAINER} 2>NUL
                        exit /b 0
                    """

                    bat """
                        "${DOCKER}" run -d ^
                            --name ${CANDIDATE_CONTAINER} ^
                            --network ${NETWORK} ^
                            -p ${CANDIDATE_PORT}:5000 ^
                            -e APP_VERSION=${VERSION} ^
                            -e ENVIRONMENT=PRODUCTION ^
                            ${APP_NAME}:${VERSION}

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
                    "${DOCKER}" inspect ${CANDIDATE_CONTAINER}

                    if errorlevel 1 (
                        echo ERROR: Candidate container does not exist
                        exit /b 1
                    )
                """

                script {

                    def running = bat(
                        script: """
                            @echo off
                            "${DOCKER}" inspect -f "{{.State.Running}}" ${CANDIDATE_CONTAINER}
                        """,
                        returnStdout: true
                    ).trim()

                    echo "Candidate running status: ${running}"

                    if (running != 'true') {
                        error('Candidate container is not running.')
                    }

                    echo 'Candidate container validation successful.'
                }
            }
        }


        stage('Application Health Check') {
            steps {
                echo '========== APPLICATION HEALTH CHECK =========='

                bat """
                    powershell -Command "try {
                        \$r=Invoke-WebRequest -Uri 'http://localhost:%CANDIDATE_PORT%/health' -UseBasicParsing -TimeoutSec 10;
                        Write-Host \$r.Content;

                        if (\$r.StatusCode -ne 200) {
                            Write-Host 'ERROR: Health check returned non-200';
                            exit 1
                        }

                        Write-Host 'Application health check successful.'
                    }
                    catch {
                        Write-Host 'ERROR: Health check failed';
                        Write-Host \$_.Exception.Message;
                        exit 1
                    }"
                """
            }
        }


        stage('Application Version Check') {
            steps {
                echo '========== APPLICATION VERSION CHECK =========='

                bat """
                    powershell -Command "try {
                        \$r=Invoke-WebRequest -Uri 'http://localhost:%CANDIDATE_PORT%/' -UseBasicParsing -TimeoutSec 10;

                        Write-Host 'APPLICATION RESPONSE:';
                        Write-Host \$r.Content;

                        \$json=\$r.Content | ConvertFrom-Json;

                        if (\$json.version -ne '%VERSION%') {
                            Write-Host 'ERROR: Application version mismatch';
                            Write-Host ('Expected: %VERSION%');
                            Write-Host ('Actual: ' + \$json.version);
                            exit 1
                        }

                        Write-Host 'Application version validation successful.'
                    }
                    catch {
                        Write-Host 'ERROR: Version check failed';
                        Write-Host \$_.Exception.Message;
                        exit 1
                    }"
                """
            }
        }


        stage('Integration Check') {
            steps {
                echo '========== INTEGRATION CHECK =========='

                bat """
                    "${DOCKER}" exec ${CANDIDATE_CONTAINER} python -c "import socket; s=socket.create_connection(('%DB_CONTAINER%',3306),5); print('DATABASE CONNECTION SUCCESS'); s.close()"

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
                    echo "Current production : ${env.CURRENT_CONTAINER}"
                    echo "Candidate           : ${env.CANDIDATE_CONTAINER}"

                    echo 'Candidate validation completed successfully.'
                    echo 'Switching production to candidate...'

                    bat """
                        "${DOCKER}" stop ${CURRENT_CONTAINER}

                        if errorlevel 1 (
                            echo ERROR: Failed to stop current production container
                            exit /b 1
                        )

                        "${DOCKER}" rm ${CURRENT_CONTAINER}

                        if errorlevel 1 (
                            echo ERROR: Failed to remove old production container
                            exit /b 1
                        )

                        echo Old production container removed.
                        echo Candidate is now the active production container.
                    """

                    env.TRAFFIC_SWITCHED = 'true'
                }
            }
        }


        stage('Deployment Verification') {
            steps {
                echo '========== DEPLOYMENT VERIFICATION =========='

                bat """
                    powershell -Command "try {
                        \$r=Invoke-WebRequest -Uri 'http://localhost:%CANDIDATE_PORT%/' -UseBasicParsing -TimeoutSec 10;

                        Write-Host 'PRODUCTION RESPONSE:';
                        Write-Host \$r.Content;

                        \$json=\$r.Content | ConvertFrom-Json;

                        if (\$json.version -ne '%VERSION%') {
                            Write-Host 'ERROR: Production version verification failed';
                            exit 1
                        }

                        Write-Host 'Production deployment verification successful.'
                    }
                    catch {
                        Write-Host 'ERROR: Production verification failed';
                        Write-Host \$_.Exception.Message;
                        exit 1
                    }"
                """
            }
        }


        stage('Production Container Status') {
            steps {
                echo '========== PRODUCTION CONTAINER STATUS =========='

                bat """
                    "${DOCKER}" ps --filter "name=orders"

                    echo.
                    echo ===== ACTIVE PRODUCTION =====

                    "${DOCKER}" ps --filter "name=%CANDIDATE_CONTAINER%"
                """
            }
        }
    }


    post {

        success {
            echo '========================================'
            echo 'BLUE-GREEN DEPLOYMENT SUCCESSFUL'
            echo '========================================'

            echo "Application : ${APP_NAME}"
            echo "Version     : ${VERSION}"
            echo "Git SHA     : ${GIT_SHA}"
            echo "Active Color: ${CANDIDATE_COLOR}"
            echo "Active Port : ${CANDIDATE_PORT}"

            bat """
                echo.
                echo ===== FINAL CONTAINERS =====
                "${DOCKER}" ps -a --filter "name=orders"

                echo.
                echo ===== NETWORK =====
                "${DOCKER}" network inspect ${NETWORK}
            """
        }


        failure {
            echo '========================================'
            echo 'BLUE-GREEN DEPLOYMENT FAILED'
            echo '========================================'

            echo "Application : ${APP_NAME}"
            echo "Version     : ${VERSION}"

            script {

                if (env.CANDIDATE_CONTAINER?.trim()) {

                    bat """
                        echo.
                        echo ===== CANDIDATE CLEANUP =====

                        "${DOCKER}" rm -f ${CANDIDATE_CONTAINER} 2>NUL

                        echo Candidate cleanup completed.
                    """
                }

                bat """
                    echo.
                    echo ===== ALL ORDERS CONTAINERS =====
                    "${DOCKER}" ps -a --filter "name=orders"

                    echo.
                    echo ===== NETWORK =====
                    "${DOCKER}" network inspect ${NETWORK}
                """

                if (env.CANDIDATE_CONTAINER?.trim()) {

                    bat """
                        echo.
                        echo ===== CANDIDATE LOGS =====
                        "${DOCKER}" logs ${CANDIDATE_CONTAINER} 2>NUL
                    """
                }

                if (env.CURRENT_CONTAINER?.trim()) {

                    bat """
                        echo.
                        echo ===== CURRENT PRODUCTION LOGS =====
                        "${DOCKER}" logs ${CURRENT_CONTAINER} 2>NUL
                    """
                }
            }
        }


        always {
            echo 'Pipeline execution completed.'
        }
    }
}