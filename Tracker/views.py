from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import JsonResponse
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from django.core.files.storage import default_storage
import gridfs
import os
from gridfs import GridFS
from pymongo import MongoClient
from django.conf import settings
from datetime import datetime

#files and images post
# Initialize MongoDB connection

@api_view(['POST'])
def upload_content(request):
    client = MongoClient('mongodb://3.109.210.34:27017/')
    db = client['Tracker']
    fs = gridfs.GridFS(db)
    response_data = {}

    # Extract card-related details from the request
    cardId = request.POST.get('cardId')
    cardName = request.POST.get('cardName')
    boardId = request.POST.get('boardId')
    employeeId = request.POST.get('employeeId')
    employeeName = request.POST.get('employeeName')

    # Handle file upload
    if 'file' in request.FILES:
        file = request.FILES['file']
        file_id = fs.put(file, filename=file.name,cardId=cardId,cardName=cardName,boardId=boardId,employeeId=employeeId,employeeName=employeeName, cardcontent_type=file.content_type)
        response_data['file_id'] = str(file_id)

    # Handle image upload
    if 'image' in request.FILES:
        image = request.FILES['image']
        image_id = fs.put(image, filename=image.name,cardId=cardId,cardName=cardName,boardId=boardId,employeeId=employeeId,employeeName=employeeName, content_type=image.content_type)
        response_data['image_id'] = str(image_id)

    # Check if any file or image was uploaded
    if not response_data:
        return Response({'error': 'No file or image provided'}, status=400)

    return Response(response_data, status=201)


from django.http import HttpResponse, Http404, JsonResponse
from gridfs.errors import NoFile
from rest_framework.decorators import api_view
import datetime
from pymongo.errors import PyMongoError
@api_view(['GET'])
def get_file(request, board_id, card_id):
    client = MongoClient('mongodb://3.109.210.34:27017/')
    db = client['Tracker']
    fs = gridfs.GridFS(db)
    try:
        # Query to find all files related to the given boardId and cardId
        files = list(fs.find({"boardId": board_id, "cardId": card_id}))
        
        # If no files are found, return an empty list
        if not files:
            return JsonResponse([], safe=False)
        
        # List to store file details
        files_data = [
            {
                "filename": file.filename,
                "cardId": file.cardId,
                "cardName": file.cardName,
                "boardId": file.boardId,
                "employeeId": file.employeeId,
                "employeeName": file.employeeName,
                "contentType": file.content_type,
                "uploadDate": file.uploadDate.strftime("%Y-%m-%d %H:%M:%S") if isinstance(file.uploadDate, datetime.datetime) else "Invalid Date"
            }
            for file in files
        ]
        
        return JsonResponse(files_data, safe=False)
    
    except PyMongoError:
        raise Http404("Error retrieving files")

#get the files and images

@api_view(['GET'])
def get_files(request):
    client = MongoClient('mongodb://3.109.210.34:27017/')
    db = client['Tracker']
    fs = gridfs.GridFS(db)
    filename = request.GET.get('filename')  # Retrieve filename from query parameters
    try:
        file = fs.find_one({"filename": filename})
        if not file:
            raise Http404("File not found")
        
        response = HttpResponse(file.read(), content_type=file.content_type)
        response['Content-Disposition'] = f'attachment; filename="{file.filename}"'
        
        # Optionally, you can add file metadata to the response headers
        response['X-File-Metadata'] = json.dumps({
            "filename": file.filename,
            "cardId": file.cardId,
            "cardName": file.cardName,
            "boardId": file.boardId,
            "employeeId": file.employeeId,
            "employeeName": file.employeeName,
            "contentType": file.content_type,
            "uploadDate": file.uploadDate.strftime("%Y-%m-%d %H:%M:%S") if isinstance(file.uploadDate, datetime.datetime) else "Invalid Date"
        })
        
        return response
    except PyMongoError:
        raise Http404("File not found")


from django.http import JsonResponse
from rest_framework.decorators import api_view
from pymongo import MongoClient
import gridfs

# Setup MongoDB connection


def delete_file_from_gridfs(filename, board_id, card_id):
    client = MongoClient('mongodb://3.109.210.34:27017/')
    db = client['Tracker']
    fs = gridfs.GridFS(db)
    # Find the file in GridFS
    file_data = db.fs.files.find_one({'filename': filename, 'boardId': board_id, 'cardId': card_id})
    if file_data:
        # Delete the file from GridFS
        fs.delete(file_data['_id'])
        print(f"File {filename} deleted successfully.")
    else:
        print(f"File {filename} not found.")

@api_view(['DELETE'])
def delete_file(request, board_id, card_id, filename):
    if request.method == 'DELETE':
        if filename and board_id and card_id:
            delete_file_from_gridfs(filename, board_id, card_id)
            return JsonResponse({'status': 'success'}, status=200)
        else:
            return JsonResponse({'status': 'error', 'message': 'Missing parameters'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)




#Register

from .serializers import EmployeeSerializer
@csrf_exempt
@api_view(['POST'])
def RegisterView(request):
    serializer = EmployeeSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Registration successful!'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#Login check through email and password
from django.contrib.auth.hashers import check_password
from .models import Employee
@csrf_exempt
@api_view(['POST'])
def LoginView(request):
    email = request.data.get('email')
    password = request.data.get('password')
    try:
        # Find the user by email
        user = Employee.objects.get(email=email)
        # Check if the password matches
        if check_password(password, user.password):
            # If password matches, login is successful
            return JsonResponse({'message': 'Login successful!', 'employeeId': user.employeeId, 'employeeName': user.employeeName, 'email': user.email}, status=status.HTTP_200_OK)
        else:
            # If password doesn't match
            return JsonResponse({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    except Employee.DoesNotExist:
        # If user with given email does not exist
        return JsonResponse({'error': 'User does not exist'}, status=status.HTTP_404_NOT_FOUND)
    


        
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Card
from .serializers import CardSerializer
from django.views.decorators.csrf import csrf_exempt

from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

@csrf_exempt
@api_view(['POST', 'GET', 'DELETE', 'PATCH'])
def CardCreateView(request, card_id=None):
    employee_id = request.query_params.get('employeeId', None)

    # Handle POST request
    if request.method == 'POST':
        serializer = CardSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Handle GET request
    elif request.method == 'GET':
        board_id = request.query_params.get('boardId', None)

        if card_id:
            card = get_object_or_404(Card, cardId=card_id, boardId=board_id)
            serializer = CardSerializer(card)
            return Response(serializer.data)
        else:
            cards = Card.objects.filter(boardId=board_id)

            # Filter by employee ID if provided
            if employee_id:
                filtered_cards = []
                for card in cards:
                    members = card.members  # Assume this is a list of dicts
                    if members and any(member['employeeId'] == employee_id for member in members):
                        filtered_cards.append(card)
                    elif card.employeeId == employee_id:
                        filtered_cards.append(card)

                serializer = CardSerializer(filtered_cards, many=True)
            else:
                serializer = CardSerializer(cards, many=True)

            return Response(serializer.data)

    # Handle DELETE request with employee ID check
    elif request.method == 'DELETE':
        if not employee_id:
            return Response({'error': 'Employee ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        card = get_object_or_404(Card, cardId=card_id)

        # Check if the employee ID matches the card owner's employee ID
        if card.employeeId != employee_id:
            return Response({'error': 'Permission denied: You are not authorized to delete this card.'}, status=status.HTTP_403_FORBIDDEN)

        # Proceed to delete the card if the employee ID matches
        card.delete()
        return Response({'message': 'Card deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)


    # Handle PATCH request with employee ID check
    elif request.method == 'PATCH':
        if not employee_id:
            return Response({'error': 'Employee ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        card = get_object_or_404(Card, cardId=card_id)

        # Check if the employee is the card owner or in the members
        if card.employeeId != employee_id and not any(member['employeeId'] == employee_id for member in card.members):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        serializer = CardSerializer(card, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



from .models import Board
from .serializers import BoardSerializer

@csrf_exempt
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def BoardsView(request, boardId=None):
    client = MongoClient('mongodb://3.109.210.34:27017/')
    db = client['Tracker']
    fs = gridfs.GridFS(db)
    collection = db['Tracker_board']
    if request.method == 'POST':
        serializer = BoardSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Board created successfully!'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'PUT':
        if boardId is None:
            return JsonResponse({'error': 'Board ID is required to update a board.'}, status=400)
        board = collection.find_one({'boardId': boardId})
        if not board:
            return JsonResponse({'error': 'Board not found.'}, status=404)
        request_employee_id = request.data.get('employeeId')
        if board['employeeId'] != request_employee_id:
            return JsonResponse({'error': 'Unauthorized to edit this board.'}, status=403)
        updated_data = {
            'boardName': request.data.get('boardName', board['boardName']),
            'boardColor': request.data.get('boardColor', board['boardColor']),
            'employeeId': request_employee_id,
            'employeeName': request.data.get('employeeName', board['employeeName']),
        }
        result = collection.update_one({'boardId': boardId}, {'$set': updated_data})
        if result.modified_count > 0:
            return JsonResponse({'message': 'Board updated successfully!'}, status=200)
        else:
            return JsonResponse({'message': 'No changes made to the board.'}, status=200)
    elif request.method == 'DELETE':
        if boardId is None:
            return JsonResponse({'error': 'Title is required to delete a board.'}, status=400)
        board = collection.find_one({'boardId': boardId})
        if not board:
            return JsonResponse({'error': 'Board not found.'}, status=404)
        request_employee_id = request.data.get('employeeId')
        if board['employeeId'] != request_employee_id:
            return JsonResponse({'error': 'Unauthorized to delete this board.'}, status=403)
        result = collection.delete_one({'boardId': boardId})
        if result.deleted_count > 0:
            return JsonResponse({'message': 'Board deleted successfully!'}, status=204)
        else:
            return JsonResponse({'error': 'Board could not be deleted.'}, status=400)


        



#delete the card

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Card

class CardDetail(APIView):
    def delete(self, request, pk, format=None):
        try:
            card = Card.objects.get(pk=pk)
            card.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Card.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        

        


#update a card when the edit the card
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Card
import json
@csrf_exempt
def update_card(request, card_id):
    if request.method == 'PUT':
        try:
            card = Card.objects.get(cardId=card_id)
        except Card.DoesNotExist:
            return JsonResponse({'error': 'Card not found'}, status=404)

        data = json.loads(request.body)
        card.cardName = data.get('cardName', card.cardName)  # Update card name
        card.save()
        return JsonResponse({'cardId': card.cardId, 'cardName': card.cardName})


#description post and get 

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Card

@csrf_exempt
def save_description(request):
    if request.method == 'POST':
        try:
            # Parse the JSON data from the request body
            data = json.loads(request.body)

            # Get the cardId, boardId, and description from the request
            card_id = data.get('cardId')
            board_id = data.get('boardId')
            board_name = data.get('boardName')
            description = data.get('description')

            # Find the card with the given cardId and boardId
            card = Card.objects.get(cardId=card_id, boardId=board_id,boardName= board_name)

            # Update the description
            card.description = description
            card.save()

            return JsonResponse({"message": "Description updated successfully"})
        except Card.DoesNotExist:
            return JsonResponse({"error": "Card not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    elif request.method == 'GET':
        try:
            # Get cardId and boardId from request parameters
            card_id = request.GET.get('cardId')
            board_id = request.GET.get('boardId')

            # Find the card with the given cardId and boardId
            card = Card.objects.get(cardId=card_id, boardId=board_id)

            # Return the description in the response
            return JsonResponse({
                "cardId": card.cardId,
                "boardId": card.boardId,
                "description": card.description
            })
        except Card.DoesNotExist:
            return JsonResponse({"error": "Card not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Card
import json

@csrf_exempt
def save_comment(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            cardId = data.get('cardId')
            boardId = data.get('boardId')  # Ensure you're using the correct field name

            # Fetch the card based on cardId and boardId
            card = Card.objects.get(cardId=cardId, boardId=boardId)

            new_comment = {
                "empid": data.get("employeeId"),
                "empname": data.get("employeeName"),
                "commenttext": data.get("text"),
                "date": data.get("date"),
                "time": data.get("time")
            }

            # If card.comment is None, initialize it as an empty list
            if card.comment is None:
                card.comment = []

            # Ensure card.comment is a list
            if not isinstance(card.comment, list):
                try:
                    card.comment = json.loads(card.comment)  # Attempt to parse it as a list
                except (json.JSONDecodeError, TypeError):
                    card.comment = []  # Initialize as an empty list if it's invalid

            # Append the new comment to the existing comments
            card.comment.append(new_comment)
            card.save()

            return JsonResponse({"message": "Comment saved successfully!"}, status=200)
        except Card.DoesNotExist:
            return JsonResponse({"error": "Card not found"}, status=404)
    return JsonResponse({"error": "Invalid request method"}, status=400)


@csrf_exempt
def get_comments(request):
    if request.method == "GET":
        try:
            cardId = request.GET.get('cardId')
            boardId = request.GET.get('boardId')

            # Fetch the card based on cardId and boardId
            card = Card.objects.get(cardId=cardId, boardId=boardId)

            # If comments are None, return an empty list
            comments = card.comment if card.comment is not None else []

            return JsonResponse({"comments": comments}, status=200)

        except Card.DoesNotExist:
            return JsonResponse({"error": "Card not found"}, status=404)
    return JsonResponse({"error": "Invalid request method"}, status=400)


@csrf_exempt
def delete_comment(request):
    if request.method == "DELETE":
        try:
            data = json.loads(request.body)
            cardId = data.get('cardId')
            boardId = data.get('boardId')
            commenttext = data.get('commenttext')

            # Fetch the card based on cardId and boardId
            card = Card.objects.get(cardId=cardId, boardId=boardId)

            # Ensure card.comment is a list
            if not isinstance(card.comment, list):
                try:
                    card.comment = json.loads(card.comment)  # Attempt to parse it as a list
                except (json.JSONDecodeError, TypeError):
                    return JsonResponse({"error": "Invalid comment format"}, status=400)

            # Find and remove the comment with the matching commenttext
            updated_comments = [comment for comment in card.comment if comment.get('commenttext') != commenttext]

            if len(updated_comments) == len(card.comment):
                return JsonResponse({"error": "Comment not found"}, status=404)

            # Update the card with the new list of comments
            card.comment = updated_comments
            card.save()

            return JsonResponse({"message": "Comment deleted successfully!"}, status=200)

        except Card.DoesNotExist:
            return JsonResponse({"error": "Card not found"}, status=404)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
    return JsonResponse({"error": "Invalid request method"}, status=400)


import logging
import json
logger = logging.getLogger(__name__)
@api_view(['GET'])
def GetBoardsView(request):
    employee_id = request.GET.get('employeeId')  # Employee ID from the logged-in employee

    if not employee_id:
        return JsonResponse({'error': 'Employee ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        logger.debug(f"Fetching boards for employee: {employee_id}")

        # Fetch boards created by the employee
        boards_created_by_employee = Board.objects.filter(employeeId=employee_id)
        logger.debug(f"Boards created by employee: {list(boards_created_by_employee.values('boardId'))}")

        # Fetch cards where the employee is a member or the card creator
        cards_where_employee_is_member = []
        for card in Card.objects.all():
            members = card.members  # Assume members is a list or None
            if members:  # If members exist, check if the employee is a member
                if any(member.get('employeeId') == employee_id for member in members):
                    cards_where_employee_is_member.append(card)
            else:  # If members is None, include only the creator of the card
                if card.employeeId == employee_id:
                    cards_where_employee_is_member.append(card)

        logger.debug(f"Cards where employee {employee_id} is a member or creator: {[card.boardId for card in cards_where_employee_is_member]}")

        # Get board IDs from the filtered cards
        board_ids_from_cards = set(card.boardId for card in cards_where_employee_is_member)

        if board_ids_from_cards:
            boards_where_employee_is_member = Board.objects.filter(boardId__in=board_ids_from_cards)
            logger.debug(f"Boards where employee is a member: {list(boards_where_employee_is_member.values('boardId'))}")
        else:
            boards_where_employee_is_member = Board.objects.none()

        # Combine both querysets (boards created + boards where employee is a member) and remove duplicates
        combined_boards = boards_created_by_employee | boards_where_employee_is_member
        combined_boards = combined_boards.distinct()
        logger.debug(f"Combined boards: {list(combined_boards.values('boardId'))}")

        # Serialize the combined queryset
        serializer = BoardSerializer(combined_boards, many=True)
        logger.debug(f"Serialized data: {serializer.data}")

        return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error in GetBoardsView: {str(e)}")
        return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
@csrf_exempt
@api_view(['GET'])
def get_all_employees(request):
    employees = Employee.objects.all().values('employeeId', 'employeeName')
    return JsonResponse(list(employees), safe=False)


from .models import Card
@csrf_exempt
@api_view(['GET', 'POST', 'DELETE'])
def add_member_to_card(request):
    card_id = request.data.get('cardId') or request.query_params.get('cardId')
    
    # Check if the card exists
    try:
        card = Card.objects.get(cardId=card_id)
    except Card.DoesNotExist:
        return Response({'error': 'Card not found.'}, status=status.HTTP_404_NOT_FOUND)

    # Handle GET request (Fetch members)
    if request.method == 'GET':
        members = card.members if card.members else []
        return Response(members, status=status.HTTP_200_OK)

    # Handle POST request (Add a member)
    if request.method == 'POST':
        employee_id = request.data.get('employeeId')
        employee_name = request.data.get('employeeName')

        if card.members is None:
            card.members = []

        if any(member['employeeId'] == employee_id for member in card.members):
            return Response({'error': 'This member is already added to the card.'}, status=status.HTTP_400_BAD_REQUEST)

        card.members.append({
            'employeeId': employee_id,
            'employeeName': employee_name,
        })
        card.save()

        return Response({'message': 'Member added successfully!'}, status=status.HTTP_201_CREATED)

    # Handle DELETE request (Remove a member)
    if request.method == 'DELETE':
        employee_id = request.query_params.get('employeeId')

        if card.members is None or not any(member['employeeId'] == employee_id for member in card.members):
            return Response({'error': 'Member not found in the card.'}, status=status.HTTP_404_NOT_FOUND)

        # Remove the member from the list
        card.members = [member for member in card.members if member['employeeId'] != employee_id]
        card.save()

        return Response({'message': 'Member removed successfully!'}, status=status.HTTP_200_OK)
        

from .models import Notification
@api_view(['GET'])
def get_dynamic_notifications(request):
    employee_id = request.GET.get('employeeId')
    
    if not employee_id:
        return JsonResponse({'error': 'Employee ID is required.'}, status=400)

    # Fetch cards where the employee is a member
    recent_memberships = []
    for card in Card.objects.all():
        members = card.members  # Assuming members is a list or None
        if members:
            if any(member.get('employeeId') == employee_id for member in members):
                # Compare the createdDate/createdTime or some logic to see if this is a "new" membership
                recent_memberships.append({
                    'cardId': card.cardId,
                    'cardName': card.cardName,
                    'boardId': card.boardId,
                    'message': f"You've been added to the card '{card.cardName}'."
                })

    # Return the recent memberships as dynamic notifications
    return JsonResponse(recent_memberships, safe=False, status=200)



from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Card
from .serializers import CardSerializer
@api_view(['POST'])
def update_card_dates(request):
    print("Request Data:", request.data)
    card_id = request.data.get('cardId')
    if not card_id:
        return Response({"error": "cardId is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        card = Card.objects.get(cardId=card_id)
    except Card.DoesNotExist:
        return Response({"error": "Card not found."}, status=status.HTTP_404_NOT_FOUND)

    startdate = request.data.get('startdate')
    enddate = request.data.get('enddate')
    
    if startdate:
        try:
            card.startdate = datetime.fromisoformat(startdate)
        except ValueError:
            return Response({"error": "Invalid startdate format."}, status=status.HTTP_400_BAD_REQUEST)

    if enddate:
        try:
            card.enddate = datetime.fromisoformat(enddate)
        except ValueError:
            return Response({"error": "Invalid enddate format."}, status=status.HTTP_400_BAD_REQUEST)

    card.save()
    return Response(CardSerializer(card).data, status=status.HTTP_200_OK)



@csrf_exempt
def edit_comment(request):
    if request.method == "PUT":
        try:
            data = json.loads(request.body)
            cardId = data.get('cardId')
            boardId = data.get('boardId')
            original_comment_text = data.get('originalCommentText')
            new_comment_text = data.get('newCommentText')
            # Fetch the card based on cardId and boardId
            card = Card.objects.get(cardId=cardId, boardId=boardId)
            # Ensure card.comment is a list
            if not isinstance(card.comment, list):
                try:
                    card.comment = json.loads(card.comment)  # Attempt to parse it as a list
                except (json.JSONDecodeError, TypeError):
                    return JsonResponse({"error": "Invalid comment format"}, status=400)
            # Find the comment to edit
            updated_comments = []
            comment_found = False
            for comment in card.comment:
                if comment.get('commenttext') == original_comment_text:
                    comment['commenttext'] = new_comment_text  # Update the comment text
                    comment_found = True
                updated_comments.append(comment)
            if not comment_found:
                return JsonResponse({"error": "Comment not found"}, status=404)
            # Update the card with the edited list of comments
            card.comment = updated_comments
            card.save()
            return JsonResponse({"message": "Comment updated successfully!"}, status=200)
        except Card.DoesNotExist:
            return JsonResponse({"error": "Card not found"}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
    return JsonResponse({"error": "Invalid request method"}, status=400)