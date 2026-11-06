import java.util.Properties

plugins {
    id("com.android.application")
    id("kotlin-android")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

val releaseSigningPropertiesFile = rootProject.file("key.properties")
val releaseSigningProperties = Properties().apply {
    if (releaseSigningPropertiesFile.isFile) {
        releaseSigningPropertiesFile.inputStream().use { input -> load(input) }
    }
}
val releaseSigningRequiredProperties = listOf("storeFile", "storePassword", "keyAlias", "keyPassword")
val releaseSigningConfigured = releaseSigningPropertiesFile.isFile &&
    releaseSigningRequiredProperties.all { !releaseSigningProperties.getProperty(it).isNullOrBlank() } &&
    releaseSigningProperties.getProperty("storeFile")?.let { rootProject.file(it).isFile } == true

android {
    namespace = "vn.edu.hvnh.hub"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = JavaVersion.VERSION_17.toString()
    }

    defaultConfig {
        applicationId = "vn.edu.hvnh.hub"
        // You can update the following values to match your application needs.
        // For more information, see: https://flutter.dev/to/review-gradle-config.
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    signingConfigs {
        create("release") {
            if (releaseSigningConfigured) {
                storeFile = rootProject.file(releaseSigningProperties.getProperty("storeFile"))
                storePassword = releaseSigningProperties.getProperty("storePassword")
                keyAlias = releaseSigningProperties.getProperty("keyAlias")
                keyPassword = releaseSigningProperties.getProperty("keyPassword")
            }
        }
    }

    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("release")
        }
    }
}

gradle.taskGraph.whenReady {
    val isReleasePackageTask = allTasks.any {
        it.name == "assembleRelease" || it.name == "bundleRelease"
    }
    if (isReleasePackageTask && !releaseSigningConfigured) {
        throw GradleException(
            "Release signing is not configured. Create android/key.properties and add the upload keystore before building a release."
        )
    }
}

flutter {
    source = "../.."
}
