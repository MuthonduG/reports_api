import cv2
import os
from mtcnn import MTCNN
from rest_framework import serializers
from .models import Report
import tempfile

class UserReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = '__all__'

    image_data = serializers.FileField(required=False)
    video_data = serializers.FileField(required=False)
    valid_image_extensions = ['jpg', 'jpeg', 'png']
    valid_video_extensions = ['mp4', 'avi', 'mkv']

    def validate_image_data(self, value):
        if value is not None:
            if not any(value.name.lower().endswith(ext) for ext in self.valid_image_extensions):
                raise serializers.ValidationError("Only image files (JPG, JPEG, PNG) are allowed.")
            if value.size > 52428800:  # 50 MB limit
                raise serializers.ValidationError("File size too large. Maximum is 50 MB.")
        return value

    def validate_video_data(self, value):
        if value is not None:
            if not any(value.name.lower().endswith(ext) for ext in self.valid_video_extensions):
                raise serializers.ValidationError("Only video files (MP4, AVI, MKV) are allowed.")
            if value.size > 52428800:  # 50 MB limit
                raise serializers.ValidationError("File size too large. Maximum is 50 MB.")
        return value

    def detect_faces_in_image(self, image_file):
        # Save the uploaded image temporarily
        with tempfile.NamedTemporaryFile(delete=False) as temp_image:
            temp_image.write(image_file.read())
            temp_image_path = temp_image.name

        # Load image and convert to RGB
        img = cv2.imread(temp_image_path)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Detect faces using MTCNN
        detector = MTCNN()
        results = detector.detect_faces(img_rgb)

        # Clean up the temporary file
        os.remove(temp_image_path)

        if not results:
            raise serializers.ValidationError("No faces detected in the uploaded image.")
        return results

    def detect_faces_in_video(self, video_file):
        # Save the uploaded video temporarily
        with tempfile.NamedTemporaryFile(delete=False) as temp_video:
            temp_video.write(video_file.read())
            temp_video_path = temp_video.name

        # Open video file
        cap = cv2.VideoCapture(temp_video_path)
        if not cap.isOpened():
            os.remove(temp_video_path)
            raise serializers.ValidationError("Unable to process the uploaded video.")

        detector = MTCNN()
        face_detected = False

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Convert frame to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Detect faces in the frame
            results = detector.detect_faces(frame_rgb)
            if results:
                face_detected = True
                break  # Stop after detecting the first face

        cap.release()
        os.remove(temp_video_path)

        if not face_detected:
            raise serializers.ValidationError("No faces detected in the uploaded video.")
        return "Face(s) detected in video."

    def validate(self, attrs):
        # Perform face detection for images
        if 'image_data' in attrs and attrs['image_data']:
            self.detect_faces_in_image(attrs['image_data'])

        # Perform face detection for videos
        if 'video_data' in attrs and attrs['video_data']:
            self.detect_faces_in_video(attrs['video_data'])

        return attrs
