from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import StudentClass, Subject, PdfLinks, ContentType, PdfDownloadTracker
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.conf import settings



class NcertClassesView(APIView):

    def get(self, request, *args, **kwargs):
        student_classes = StudentClass.objects.all()
        if not student_classes.exists():
            return Response({"error": "No classes found"}, status=404)

        data = [
            {"id": student_class.id, "class_name": student_class.class_name, "class_value":student_class.class_value}
            for student_class in student_classes
        ]
        return Response(data, status=status.HTTP_200_OK)


class NcertSubjectsView(APIView):

    def get(self, request):

        class_name = request.GET.get('class', None)

        if not class_name:
            return Response({"error": "class parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch the StudentClass instance
        try:
            student_class = StudentClass.objects.get(class_name=class_name)
        except StudentClass.DoesNotExist:
            return Response({"error": "Class not found"}, status=404)

        # Fetch all related subjects for the class
        subjects = Subject.objects.filter(class_name=student_class)

        # Prepare the response data
        response_data = {
            "class_value": student_class.class_value,
            "class_name": student_class.class_name,
            "subjects": [
                {
                    "id": subject.id,
                    "subject_name": subject.subject_name
                }
                for subject in subjects
            ]
        }

        return Response(response_data, status=200)



class NcertDataView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):

        class_name = request.GET.get('class', None)
        subject_names = request.GET.getlist('subject', None)

        if not class_name:
            return Response({"error": "class parameter is required"}, status=400)

        # Filter based on class_name
        try:
            student_class = StudentClass.objects.get(class_name=class_name)
        except StudentClass.DoesNotExist:
            return Response({"error": "Class not found"}, status=404)

        # Filter subjects
        subjects = Subject.objects.filter(class_name=student_class)

        if subject_names:
            subjects = subjects.filter(subject_name__in=subject_names)

        # Prepare the response data
        response_data = {
            "class_value": student_class.class_value,
            "class_name": student_class.class_name,
            "subjects": []
        }

        for subject in subjects:
            pdf_links = PdfLinks.objects.filter(subject=subject).select_related('content_type')
            subject_data = [
                {
                    "id": link.id,
                    "subject_name": subject.subject_name,
                    "content_type": link.content_type.content_type,
                    "content_name": link.content_name,
                    "action_url": request.build_absolute_uri(str(link.action_url)),
                }
                for link in pdf_links
            ]
            response_data["subjects"].extend(subject_data)

        return Response(response_data, status=200)



class TrackPdfDownloadAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request,**kwargs):
        
        email = request.GET.get('email', None)
        if not email:
            return Response(
                {'status': 'error', 'message': 'Email parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        download_records = PdfDownloadTracker.objects.filter(email=email)

        # Check if records exist for the given email
        if not download_records.exists():
            return Response(
                {'status': 'success', 'message': 'No records found for the given email'},
                status=status.HTTP_200_OK
            )

        user_id = download_records.first().user_id

        # Serialize the data for download records
        download_data = [
            {
                'pdflink_id': record.pdf_link.id,
                'content_name': record.pdf_link.content_name,
                'action_url': record.pdf_link.action_url,
                'timestamp': record.timestamp,
                'downloaded': record.downloaded
            }
            for record in download_records
        ]

        # Prepare the complete response
        return Response(
            {
                'user_id': user_id,
                'email': email,
                'data': download_data
            },
            status=status.HTTP_200_OK
        )



    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        email = request.data.get('email')
        pdf_link_id = request.data.get('pdflink_id')

        # Validate inputs
        if not (user_id and email and pdf_link_id):
            return Response(
                {'status': 'error', 'message': 'Invalid input'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the PdfLinks object
        pdf_link = get_object_or_404(PdfLinks, id=pdf_link_id)

        # Create a new record for each download
        tracker = PdfDownloadTracker.objects.create(
            user_id=user_id,
            email=email,
            pdf_link=pdf_link,
            timestamp=now(),
            downloaded=True
        )

        # Return the response
        return Response(
            {
                'status': 'success',
                'message': 'PDF downloaded successfully',
                'pdf_link': str(pdf_link.action_url),
                'downloaded_at': tracker.timestamp
            },
            status=status.HTTP_201_CREATED
        )

