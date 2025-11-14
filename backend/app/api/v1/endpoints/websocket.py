"""
Endpoints WebSocket pour synchronisation temps réel
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status
from fastapi.exceptions import HTTPException
import logging

from app.core.websocket import manager
from app.core.security import decode_token
from app.core.dependencies import get_db
from app.models.user import User
from sqlalchemy.orm import Session

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws/doctor/{doctor_id}")
async def doctor_schedule_websocket(
    websocket: WebSocket,
    doctor_id: int,
    token: str = Query(..., description="JWT access token"),
    db: Session = Depends(get_db)
):
    """
    WebSocket pour écouter les mises à jour de planning d'un docteur
    
    Les patients se connectent ici pour recevoir des notifications en temps réel
    quand un docteur modifie ses disponibilités ou qu'un créneau est réservé.
    
    **Messages reçus par le client:**
    - `connected`: Confirmation de connexion
    - `schedule_updated`: Le planning a été modifié
    - `slot_booked`: Un créneau a été réservé
    - `appointment_cancelled`: Un rendez-vous a été annulé
    
    **Query Parameters:**
    - token: JWT access token pour authentification
    """
    try:
        # Valider le token JWT
        payload = decode_token(token)
        if not payload:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Vérifier que l'utilisateur existe
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Connecter le client
        await manager.connect_doctor_listener(doctor_id, websocket)
        
        logger.info(f"✅ WebSocket établi: User {user.id} -> Doctor {doctor_id}")
        
        try:
            # Boucle de maintien de connexion
            while True:
                # Recevoir des messages (heartbeat ou commandes futures)
                data = await websocket.receive_text()
                
                # Pour l'instant, juste un keepalive
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
                
        except WebSocketDisconnect:
            logger.info(f"🔌 WebSocket déconnecté: User {user.id} -> Doctor {doctor_id}")
        finally:
            await manager.disconnect_doctor_listener(doctor_id, websocket)
            
    except Exception as e:
        logger.error(f"❌ Erreur WebSocket: {e}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except:
            pass


@router.websocket("/ws/patient/{patient_id}")
async def patient_notifications_websocket(
    websocket: WebSocket,
    patient_id: int,
    token: str = Query(..., description="JWT access token"),
    db: Session = Depends(get_db)
):
    """
    WebSocket pour notifications personnelles d'un patient
    
    Le patient reçoit des notifications sur ses propres rendez-vous:
    - Confirmations de rendez-vous
    - Rappels
    - Annulations
    - Modifications
    
    **Query Parameters:**
    - token: JWT access token pour authentification
    """
    try:
        # Valider le token JWT
        payload = decode_token(token)
        if not payload:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        user_id = payload.get("sub")
        if not user_id or int(user_id) != patient_id:
            # Vérifier que le patient accède à ses propres notifications
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Connecter le patient
        await manager.connect_patient(patient_id, websocket)
        
        logger.info(f"✅ WebSocket patient établi: Patient {patient_id}")
        
        try:
            while True:
                data = await websocket.receive_text()
                
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
                
        except WebSocketDisconnect:
            logger.info(f"🔌 WebSocket patient déconnecté: {patient_id}")
        finally:
            await manager.disconnect_patient(patient_id, websocket)
            
    except Exception as e:
        logger.error(f"❌ Erreur WebSocket patient: {e}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except:
            pass


@router.get("/ws/stats")
async def get_websocket_stats():
    """
    Obtenir les statistiques des connexions WebSocket actives
    Utile pour le monitoring
    """
    return manager.get_stats()
