"""
WebSocket Manager pour synchronisation temps réel
Gère les connexions WebSocket pour les notifications de planning
"""
import json
import logging
from datetime import datetime
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Gestionnaire de connexions WebSocket avec pub/sub Redis
    Permet la scalabilité horizontale entre plusieurs instances FastAPI
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        # Connexions actives: {doctor_id: Set[WebSocket]}
        self.doctor_connections: Dict[int, Set[WebSocket]] = {}
        
        # Connexions patients: {patient_id: Set[WebSocket]}
        self.patient_connections: Dict[int, Set[WebSocket]] = {}
        
        # Redis pub/sub pour broadcast entre instances
        self.redis_url = redis_url
        self.redis_client: Optional[aioredis.Redis] = None
        self.pubsub = None
    
    async def connect(self):
        """Initialiser la connexion Redis"""
        try:
            self.redis_client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            self.pubsub = self.redis_client.pubsub()
            await self.pubsub.subscribe("doctor_schedule_updates")
            logger.info("✅ Redis pub/sub initialisé")
        except Exception as e:
            logger.error(f"❌ Erreur connexion Redis: {e}")
            self.redis_client = None
    
    async def disconnect(self):
        """Fermer la connexion Redis"""
        if self.pubsub:
            await self.pubsub.unsubscribe("doctor_schedule_updates")
            await self.pubsub.close()
        if self.redis_client:
            await self.redis_client.close()
    
    async def connect_doctor_listener(self, doctor_id: int, websocket: WebSocket):
        """
        Connecter un client (patient) qui écoute les mises à jour d'un docteur
        """
        await websocket.accept()
        
        if doctor_id not in self.doctor_connections:
            self.doctor_connections[doctor_id] = set()
        
        self.doctor_connections[doctor_id].add(websocket)
        
        logger.info(f"🔌 Client connecté au docteur {doctor_id}. "
                   f"Total: {len(self.doctor_connections[doctor_id])} connexion(s)")
        
        # Envoyer message de confirmation
        await websocket.send_json({
            "type": "connected",
            "doctor_id": doctor_id,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def disconnect_doctor_listener(self, doctor_id: int, websocket: WebSocket):
        """Déconnecter un client"""
        if doctor_id in self.doctor_connections:
            self.doctor_connections[doctor_id].discard(websocket)
            
            # Supprimer le set s'il est vide
            if not self.doctor_connections[doctor_id]:
                del self.doctor_connections[doctor_id]
            
            logger.info(f"🔌 Client déconnecté du docteur {doctor_id}")
    
    async def connect_patient(self, patient_id: int, websocket: WebSocket):
        """Connecter un patient pour recevoir ses notifications"""
        await websocket.accept()
        
        if patient_id not in self.patient_connections:
            self.patient_connections[patient_id] = set()
        
        self.patient_connections[patient_id].add(websocket)
        
        logger.info(f"🔌 Patient {patient_id} connecté. "
                   f"Total: {len(self.patient_connections[patient_id])} connexion(s)")
    
    async def disconnect_patient(self, patient_id: int, websocket: WebSocket):
        """Déconnecter un patient"""
        if patient_id in self.patient_connections:
            self.patient_connections[patient_id].discard(websocket)
            
            if not self.patient_connections[patient_id]:
                del self.patient_connections[patient_id]
            
            logger.info(f"🔌 Patient {patient_id} déconnecté")
    
    async def notify_doctor_listeners(self, doctor_id: int, message: dict):
        """
        Envoyer une notification à tous les clients écoutant un docteur
        (ex: patients consultant les créneaux de ce docteur)
        """
        if doctor_id not in self.doctor_connections:
            return
        
        dead_connections = set()
        
        for connection in self.doctor_connections[doctor_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"⚠️ Erreur envoi message: {e}")
                dead_connections.add(connection)
        
        # Nettoyer les connexions mortes
        self.doctor_connections[doctor_id] -= dead_connections
        
        logger.info(f"📤 Notification envoyée à {len(self.doctor_connections[doctor_id])} "
                   f"client(s) du docteur {doctor_id}")
    
    async def notify_patient(self, patient_id: int, message: dict):
        """Envoyer une notification à un patient spécifique"""
        if patient_id not in self.patient_connections:
            return
        
        dead_connections = set()
        
        for connection in self.patient_connections[patient_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"⚠️ Erreur envoi message patient {patient_id}: {e}")
                dead_connections.add(connection)
        
        self.patient_connections[patient_id] -= dead_connections
        
        logger.info(f"📤 Notification envoyée au patient {patient_id}")
    
    async def broadcast_schedule_update(self, doctor_id: int, event_type: str = "schedule_updated"):
        """
        Broadcast une mise à jour de planning à tous les clients
        Utilise Redis pub/sub pour synchroniser entre instances
        """
        message = {
            "type": event_type,
            "doctor_id": doctor_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Notification locale
        await self.notify_doctor_listeners(doctor_id, message)
        
        # Broadcast via Redis pour autres instances
        if self.redis_client:
            try:
                await self.redis_client.publish(
                    "doctor_schedule_updates",
                    json.dumps(message)
                )
                logger.info(f"📡 Broadcast Redis: {event_type} pour docteur {doctor_id}")
            except Exception as e:
                logger.error(f"❌ Erreur broadcast Redis: {e}")
    
    async def broadcast_slot_booked(self, doctor_id: int, slot_id: str, patient_id: int):
        """Notifier qu'un créneau a été réservé"""
        message = {
            "type": "slot_booked",
            "doctor_id": doctor_id,
            "slot_id": slot_id,
            "patient_id": patient_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.notify_doctor_listeners(doctor_id, message)
        
        if self.redis_client:
            try:
                await self.redis_client.publish(
                    "doctor_schedule_updates",
                    json.dumps(message)
                )
            except Exception as e:
                logger.error(f"❌ Erreur broadcast slot_booked: {e}")
    
    async def broadcast_appointment_cancelled(self, doctor_id: int, appointment_id: int):
        """Notifier qu'un rendez-vous a été annulé"""
        message = {
            "type": "appointment_cancelled",
            "doctor_id": doctor_id,
            "appointment_id": appointment_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.notify_doctor_listeners(doctor_id, message)
        
        if self.redis_client:
            try:
                await self.redis_client.publish(
                    "doctor_schedule_updates",
                    json.dumps(message)
                )
            except Exception as e:
                logger.error(f"❌ Erreur broadcast appointment_cancelled: {e}")
    
    def get_stats(self) -> dict:
        """Retourner les statistiques de connexions"""
        return {
            "doctor_listeners": {
                doctor_id: len(connections)
                for doctor_id, connections in self.doctor_connections.items()
            },
            "patient_connections": {
                patient_id: len(connections)
                for patient_id, connections in self.patient_connections.items()
            },
            "total_doctor_listeners": sum(
                len(conns) for conns in self.doctor_connections.values()
            ),
            "total_patient_connections": sum(
                len(conns) for conns in self.patient_connections.values()
            )
        }


# Instance globale
manager = ConnectionManager()
