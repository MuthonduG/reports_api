from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Report
from .serializers import UserReportSerializer
from notifications.signals import notify
import logging

logger = logging.getLogger(__name__)

# Get all reports (for authenticated users)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getReports(request):
    reports = Report.objects.all()
    serializer = UserReportSerializer(reports, many=True)
    return Response(serializer.data)

# Get a specific report (for authenticated users)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getReport(request, pk):
    report = get_object_or_404(Report, id=pk)
    serializer = UserReportSerializer(report, many=False)
    return Response(serializer.data)

# Create a new report (restricted to logged-in users)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createReport(request):
    serializer = UserReportSerializer(data=request.data)
    if serializer.is_valid():
        # Associate the report with the logged-in user's primary key
        report = serializer.save(user_id=request.user.pk)
        logger.info(f"User {request.user.username} created a new report.")
        
        # Send a notification to the user
        notify.send(
            sender=request.user,
            recipient=request.user,
            verb='created a new report',
            description=f"Report titled '{report.report_title}' was successfully created.",
            action_object=report
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        logger.error(f"Report creation errors: {serializer.errors}")
        return Response(
            {"errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

# Update a report
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def updateReport(request, pk):
    report = get_object_or_404(Report, id=pk)

    # Determine permissions
    is_creator = report.user_id == request.user
    is_admin = request.user.is_staff

    data = request.data

    if is_admin:
        # Admin can only update `report_status`
        if 'report_status' in data:
            old_status = report.report_status 
            report.report_status = data['report_status']
            report.save()

            # Log the update
            logger.info(f"Admin updated report status for report {report.report_title} from '{old_status}' to '{data['report_status']}'.")

            # Send a notification to the report's creator
            notify.send(
                sender=request.user,
                recipient=report.user,  # Assuming `report.user` is the creator of the report
                verb='updated the status of your report',
                description=f"The status of your report titled '{report.report_title}' was updated to '{report.report_status}'.",
                action_object=report
            )

            return Response({"message": "Report status updated by admin."}, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": "Admins can only update the report status."},
                status=status.HTTP_403_FORBIDDEN
            )
    elif is_creator:
        # Creator can update all fields except `report_status`
        if 'report_status' in data:
            return Response(
                {"error": "You are not authorized to update the report status."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = UserReportSerializer(instance=report, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"User {request.user.username} updated report {report.report_title}.")
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            logger.error(f"Update errors for report {report.report_title}: {serializer.errors}")
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
    else:
        return Response(
            {"error": "You are not authorized to update this report."},
            status=status.HTTP_403_FORBIDDEN
        )


# Delete a report
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def deleteReport(request, pk):
    report = get_object_or_404(Report, id=pk)

    # Only the creator or an admin can delete the report
    if report.user_id == request.user or request.user.is_staff:
        report.delete()
        logger.info(f"Report {pk} deleted by user {request.user.username}.")
        return Response(
            {"message": "Report successfully deleted!"},
            status=status.HTTP_204_NO_CONTENT
        )
    else:
        return Response(
            {"error": "You are not authorized to delete this report."},
            status=status.HTTP_403_FORBIDDEN
        )