try:
    from androguard.misc import AnalyzeAPK
    print("androguard.misc.AnalyzeAPK imported successfully!")
except Exception as e:
    print(f"Error importing AnalyzeAPK: {e}")

try:
    from androguard.core.apk import APK
    print("androguard.core.apk.APK imported successfully!")
except Exception as e:
    print(f"Error importing APK: {e}")
