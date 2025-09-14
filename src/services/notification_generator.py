"""Push notification generation service using Azure OpenAI."""

import os
import json
import logging
from typing import Optional, Dict, Any
from openai import AzureOpenAI
from dotenv import load_dotenv

from src.models.client import ClientRecommendation

load_dotenv()

logger = logging.getLogger(__name__)

class NotificationGenerator:
    """Generate personalized push notifications using GPT-4."""

    def __init__(self):
        self.client = None
        self._initialize_azure_client()

    def _initialize_azure_client(self):
        """Initialize Azure OpenAI client."""
        try:
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")

            if not endpoint or not api_key:
                logger.warning("Azure OpenAI credentials not configured. Notification generation will use templates.")
                return

            self.client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version=api_version
            )

            logger.info("Azure OpenAI client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI client: {e}")
            self.client = None

    def generate_push_notification(self, recommendation: ClientRecommendation,
                                 client_data: Dict[str, Any]) -> str:
        """Generate personalized push notification."""

        if self.client:
            return self._generate_with_gpt(recommendation, client_data)
        else:
            return self._generate_with_template(recommendation, client_data)

    def _generate_with_gpt(self, recommendation: ClientRecommendation,
                          client_data: Dict[str, Any]) -> str:
        """Generate notification using GPT-4."""
        try:
            deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")

            # Prepare context for GPT
            context = self._prepare_context(recommendation, client_data)

            prompt = f"""
Сгенерируй персональное пуш-уведомление для банковского клиента на основе его данных.

КОНТЕКСТ КЛИЕНТА:
{context}

РЕКОМЕНДУЕМЫЙ ПРОДУКТ: {recommendation.product_name}
ПОТЕНЦИАЛЬНАЯ ВЫГОДА: {recommendation.potential_benefit:,.0f} ₸ в год
ПРИЧИНА РЕКОМЕНДАЦИИ: {recommendation.recommendation_reason}

ТРЕБОВАНИЯ К ТОНУ (TOV):
- На равных, просто и по-человечески
- Обращение на "вы" с маленькой буквы
- Важное — в начало, без воды
- Лёгкий, ненавязчивый тон
- Максимум 1 эмодзи по смыслу
- Длина 180-220 символов

ФОРМАТ ЧИСЕЛ:
- Дробная часть — запятая
- Разряды — пробелы (например: 27 400 ₸)

СТРУКТУРА СООБЩЕНИЯ:
1. Персональное наблюдение по тратам/поведению
2. Конкретная польза продукта
3. Призыв к действию

Сгенерируй ТОЛЬКО текст уведомления без дополнительных комментариев.
"""

            response = self.client.chat.completions.create(
                model=deployment_name,
                messages=[
                    {"role": "system", "content": "Ты — эксперт по написанию персональных банковских уведомлений в дружелюбном тоне."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )

            notification = response.choices[0].message.content.strip()

            # Validate length
            if len(notification) > 250:
                notification = notification[:247] + "..."

            return notification

        except Exception as e:
            logger.error(f"Error generating notification with GPT: {e}")
            return self._generate_with_template(recommendation, client_data)

    def _generate_with_template(self, recommendation: ClientRecommendation,
                               client_data: Dict[str, Any]) -> str:
        """Generate notification using predefined templates."""

        name = recommendation.client_name
        product = recommendation.product_name
        benefit = recommendation.potential_benefit

        # Template-based generation based on product type
        if product == "Карта для путешествий":
            travel_spending = client_data.get('travel_spending_3m', 0)
            return f"{name}, за 3 месяца вы потратили {travel_spending:,.0f} ₸ на поездки и такси. С картой для путешествий вернули бы {benefit/4:,.0f} ₸ кешбэком. Оформить карту"

        elif product == "Премиальная карта":
            balance = client_data.get('avg_monthly_balance_kzt', 0)
            if balance > 1000000:
                return f"{name}, у вас стабильно высокий остаток на счёте. Премиальная карта даст повышенный кешбэк и бесплатные снятия. Экономия {benefit:,.0f} ₸/год. Подключить"
            else:
                return f"{name}, ваши траты в ресторанах и на покупках дают право на премиальную карту с повышенным кешбэком. Потенциальная выгода {benefit:,.0f} ₸/год. Оформить"

        elif product == "Кредитная карта":
            top_categories = client_data.get('top_categories', ['покупки'])
            cat1, cat2 = (top_categories[:2] + ['', ''])[:2]
            categories_str = f"{cat1}, {cat2}".rstrip(', ')
            return f"{name}, ваши топ-категории — {categories_str}. Кредитная карта даст до 10% кешбэк. Выгода {benefit:,.0f} ₸/год. Оформить карту"

        elif product == "Обмен валют":
            fx_volume = client_data.get('fx_volume_3m', 0)
            return f"{name}, вы активно работаете с валютой (оборот {fx_volume:,.0f} ₸). Выгодный обмен в приложении сэкономит {benefit:,.0f} ₸/год. Настроить обмен"

        elif product == "Кредит наличными":
            return f"{name}, если нужны средства на крупные расходы — кредит наличными с гибкими условиями. Экономия на процентах {benefit:,.0f} ₸/год. Узнать лимит"

        elif "Депозит" in product:
            if "Сберегательный" in product:
                rate = "16,5%"
            elif "Накопительный" in product:
                rate = "15,5%"
            else:
                rate = "14,5%"

            return f"{name}, у вас есть свободные средства. Размещение на депозите {rate} годовых принесёт {benefit:,.0f} ₸ дохода. Открыть вклад"

        elif product == "Инвестиции":
            return f"{name}, попробуйте инвестиции с низким порогом входа и без комиссий на старт. Потенциальная экономия {benefit:,.0f} ₸/год. Открыть счёт"

        elif product == "Золотые слитки":
            return f"{name}, для диверсификации портфеля рассмотрите золотые слитки. Защита от инфляции на сумму {benefit:,.0f} ₸/год. Узнать подробнее"

        else:
            return f"{name}, рекомендуем {product} с потенциальной выгодой {benefit:,.0f} ₸ в год. Узнать условия"

    def _prepare_context(self, recommendation: ClientRecommendation,
                        client_data: Dict[str, Any]) -> str:
        """Prepare client context for GPT prompt."""

        context_parts = [
            f"Имя: {recommendation.client_name}",
            f"Текущий продукт: {recommendation.current_product or 'Не указан'}",
        ]

        # Add relevant behavioral data
        if 'avg_monthly_balance_kzt' in client_data:
            balance = client_data['avg_monthly_balance_kzt']
            context_parts.append(f"Средний остаток: {balance:,.0f} ₸")

        if 'total_spending_3m' in client_data:
            spending = client_data['total_spending_3m']
            context_parts.append(f"Траты за 3 мес: {spending:,.0f} ₸")

        if 'top_categories' in client_data:
            categories = client_data['top_categories'][:3]
            context_parts.append(f"Топ-категории: {', '.join(categories)}")

        if 'travel_spending_3m' in client_data and client_data['travel_spending_3m'] > 0:
            travel = client_data['travel_spending_3m']
            context_parts.append(f"Траты на поездки: {travel:,.0f} ₸")

        if 'fx_activity_score' in client_data and client_data['fx_activity_score'] > 0:
            context_parts.append(f"Валютная активность: высокая")

        return "\n".join(context_parts)

    def generate_for_all_recommendations(self) -> Dict[int, str]:
        """Generate notifications for all client recommendations."""
        from src.utils.database import db_manager
        from sqlalchemy import text

        session = db_manager.get_session()
        notifications = {}

        try:
            # Get all top recommendations with client data
            result = session.execute(text("""
                SELECT c.client_code, c.name, p.name as product_name,
                       cr.potential_benefit, cr.recommendation_reason,
                       c.avg_monthly_balance_kzt
                FROM client_recommendations cr
                JOIN clients c ON cr.client_code = c.client_code
                JOIN products p ON cr.product_id = p.id
                WHERE cr.rank = 1
                ORDER BY c.client_code
            """)).fetchall()

            for row in result:
                recommendation = ClientRecommendation(
                    client_code=row.client_code,
                    client_name=row.name,
                    current_product=None,
                    rank=1,
                    product_name=row.product_name,
                    potential_benefit=row.potential_benefit,
                    recommendation_reason=row.recommendation_reason,
                    confidence_score=0.8
                )

                client_data = {
                    'avg_monthly_balance_kzt': float(row.avg_monthly_balance_kzt)
                }

                notification = self.generate_push_notification(recommendation, client_data)
                notifications[row.client_code] = notification

            logger.info(f"Generated {len(notifications)} push notifications")

        except Exception as e:
            logger.error(f"Error generating notifications: {e}")

        finally:
            session.close()

        return notifications

    def _load_prompt_template(self) -> str:
        """Load prompt template from prompt.md file."""
        try:
            prompt_path = '/app/prompt.md'
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error loading prompt template: {e}")
            # Fallback to basic prompt
            return """
Сгенерируй персональное пуш-уведомление для банковского клиента на основе его данных.

ДАННЫЕ КЛИЕНТА:
{client_data}

Создай короткое (180-220 символов) персональное уведомление с:
1. Персональным наблюдением по тратам
2. Конкретной пользой продукта
3. Призывом к действию

Верни ТОЛЬКО текст уведомления.
"""

    def _get_client_data_for_notification(self, client_code: int) -> str:
        """Get detailed client data using the provided SQL query."""
        from src.utils.database import db_manager
        from sqlalchemy import text

        session = db_manager.get_session()
        try:
            # Execute the provided SQL query
            result = session.execute(text("""
                SELECT
                      u.client_code, u.name as client_name, u.status client_status, u.age, u.city,
                      p.name as product_name, p.description as product_description, cr.rank as top_level, cr.potential_benefit, cr.recommendation_reason,
                      pb.calculation_details
                FROM clients u
                LEFT JOIN client_recommendations cr ON u.client_code = cr.client_code
                LEFT JOIN products p ON cr.product_id = p.id
                LEFT JOIN product_benefits pb ON pb.client_code = u.client_code AND pb.product_id = p.id
                WHERE u.client_code = :client_code
                ORDER BY u.client_code, cr.rank
            """), {'client_code': client_code}).fetchall()

            if not result:
                return ""

            # Convert SQL result to JSON format
            client_data_list = []

            for row in result:
                if row.product_name:  # Only include rows with product data
                    # Parse calculation_details from JSON string if it's a string
                    calculation_details = row.calculation_details
                    if isinstance(calculation_details, str):
                        try:
                            calculation_details = json.loads(calculation_details)
                        except (json.JSONDecodeError, TypeError):
                            calculation_details = {}

                    client_data_list.append({
                        "client_code": row.client_code,
                        "client_name": row.client_name,
                        "client_status": row.client_status,
                        "age": row.age,
                        "city": row.city,
                        "product_name": row.product_name,
                        "product_description": row.product_description,
                        "top_level": row.top_level,
                        "potential_benefit": float(row.potential_benefit),
                        "recommendation_reason": row.recommendation_reason,
                        "calculation_details": calculation_details or {}
                    })

            # Return JSON string
            return json.dumps(client_data_list, ensure_ascii=False, indent=2)

        finally:
            session.close()

    def _get_recommendation_data_by_id(self, recommendation_id: int) -> str:
        """Get recommendation data by recommendation ID for single recommendation processing."""
        from src.utils.database import db_manager
        from sqlalchemy import text

        session = db_manager.get_session()
        try:
            # Execute SQL query with specific recommendation ID
            result = session.execute(text("""
                SELECT
                      u.client_code, u.name as client_name, u.status client_status, u.age, u.city,
                      p.name as product_name, p.description as product_description, cr.rank as top_level, cr.potential_benefit, cr.recommendation_reason,
                      pb.calculation_details
                FROM clients u
                LEFT JOIN client_recommendations cr ON u.client_code = cr.client_code
                LEFT JOIN products p ON cr.product_id = p.id
                LEFT JOIN product_benefits pb ON pb.client_code = u.client_code AND pb.product_id = p.id
                WHERE cr.id = :recommendation_id
                ORDER BY u.client_code, cr.rank
            """), {'recommendation_id': recommendation_id}).fetchone()

            if not result:
                logger.warning(f"No data found for recommendation ID {recommendation_id}")
                return ""

            # Parse calculation_details from JSON string if it's a string
            calculation_details = result.calculation_details
            if isinstance(calculation_details, str):
                try:
                    calculation_details = json.loads(calculation_details)
                except (json.JSONDecodeError, TypeError):
                    calculation_details = {}

            # Create JSON object for single recommendation
            recommendation_data = {
                "client_code": result.client_code,
                "client_name": result.client_name,
                "client_status": result.client_status,
                "age": result.age,
                "city": result.city,
                "product_name": result.product_name,
                "product_description": result.product_description,
                "top_level": result.top_level,
                "potential_benefit": float(result.potential_benefit),
                "recommendation_reason": result.recommendation_reason,
                "calculation_details": calculation_details or {}
            }

            # Return JSON string
            return json.dumps(recommendation_data, ensure_ascii=False, indent=2)

        finally:
            session.close()

    def generate_and_save_notification(self, client_code: int) -> bool:
        """Generate push notification for a client and save it to database."""
        try:
            # Load prompt template
            prompt_template = self._load_prompt_template()

            # Get client data
            client_data = self._get_client_data_for_notification(client_code)
            if not client_data:
                logger.warning(f"No data found for client {client_code}")
                return False

            # Generate notification using Azure OpenAI
            if self.client:
                notification = self._generate_notification_with_azure_openai(prompt_template, client_data)
            else:
                logger.warning("Azure OpenAI not configured, using template fallback")
                notification = f"Персональная рекомендация для клиента {client_code}"

            # Save notification to database
            return self._save_notification_to_database(client_code, notification)

        except Exception as e:
            logger.error(f"Error generating notification for client {client_code}: {e}")
            return False

    def generate_and_save_notification_by_id(self, recommendation_id: int) -> bool:
        """Generate push notification for a specific recommendation and save it to database."""
        try:
            # Load prompt template
            prompt_template = self._load_prompt_template()

            # Get recommendation data by ID
            recommendation_data = self._get_recommendation_data_by_id(recommendation_id)
            if not recommendation_data:
                logger.warning(f"No data found for recommendation ID {recommendation_id}")
                return False

            # Generate notification using Azure OpenAI
            if self.client:
                notification = self._generate_notification_with_azure_openai(prompt_template, recommendation_data)
            else:
                logger.warning("Azure OpenAI not configured, using template fallback")
                notification = f"Персональная рекомендация для записи {recommendation_id}"

            # Save notification to database by recommendation ID
            return self._save_notification_to_database_by_id(recommendation_id, notification)

        except Exception as e:
            logger.error(f"Error generating notification for recommendation {recommendation_id}: {e}")
            return False

    def _generate_notification_with_azure_openai(self, prompt_template: str, client_data: str) -> str:
        """Generate notification using Azure OpenAI."""
        try:
            deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")

            # Format prompt with client data
            full_prompt = prompt_template.replace("{client_data}", client_data)

            response = self.client.chat.completions.create(
                model=deployment_name,
                messages=[
                    {"role": "system", "content": "Ты — эксперт по написанию персональных банковских уведомлений."},
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )

            notification = response.choices[0].message.content.strip()

            # Clean up the notification - remove quotes if present
            if notification.startswith('"') and notification.endswith('"'):
                notification = notification[1:-1]

            # Validate length (180-220 characters target)
            if len(notification) > 250:
                notification = notification[:247] + "..."

            return notification

        except Exception as e:
            logger.error(f"Error calling Azure OpenAI: {e}")
            return "Персональная рекомендация банковского продукта"

    def _save_notification_to_database(self, client_code: int, notification: str) -> bool:
        """Save generated notification to client_recommendations.push_notification field."""
        from src.utils.database import db_manager
        from sqlalchemy import text

        session = db_manager.get_session()
        try:
            # Update the top recommendation (rank = 1) with the notification
            session.execute(text("""
                UPDATE client_recommendations
                SET push_notification = :notification
                WHERE client_code = :client_code AND rank = 1
            """), {
                'client_code': client_code,
                'notification': notification
            })

            session.commit()
            logger.debug(f"Saved notification for client {client_code}: {notification}")
            return True

        except Exception as e:
            logger.error(f"Error saving notification to database: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def _save_notification_to_database_by_id(self, recommendation_id: int, notification: str) -> bool:
        """Save generated notification to specific client_recommendations record by ID."""
        from src.utils.database import db_manager
        from sqlalchemy import text

        session = db_manager.get_session()
        try:
            # Update the specific recommendation with the notification
            session.execute(text("""
                UPDATE client_recommendations
                SET push_notification = :notification
                WHERE id = :recommendation_id
            """), {
                'recommendation_id': recommendation_id,
                'notification': notification
            })

            session.commit()
            logger.debug(f"Saved notification for recommendation {recommendation_id}: {notification}")
            return True

        except Exception as e:
            logger.error(f"Error saving notification to database: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def close(self):
        """Close any resources."""
        pass