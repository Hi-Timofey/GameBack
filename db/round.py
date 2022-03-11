import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext.hybrid import hybrid_method
from .move import Choice


from .database import SqlAlchemyBase


class Round(SqlAlchemyBase):
    __tablename__ = "rounds"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    round_number = sa.Column(sa.Integer)

    winner_user_address = sa.Column(
        sa.String(42), sa.ForeignKey("users.address"), nullable=True, default=None
    )

    winner_sid = sa.Column(sa.String, nullable=True, default=None)

    battle_id = sa.Column(sa.Integer, sa.ForeignKey("battles.id"))
    battle = orm.relationship("Battle")

    moves = orm.relationship("Move", back_populates="round")

    @hybrid_method
    def get_move_of_address(self, address: str):
        for move in self.moves:
            if move.owner_address == address:
                return move
        raise ValueError("not found move with such address")

    @hybrid_method
    def set_winner_user_address(self):  # noqa
        if len(self.moves) == 2:
            # Player2 is a player who made last move so his sid is in "sid" var
            player1 = self.moves[0]  # != sid
            player2 = self.moves[1]  # sid

            # Game logic
            if player1.choice == player2.choice:
                self.winner_user_address = "no_one"
            else:
                if player1.choice == Choice.attack:
                    if player2.choice == Choice.trick:
                        self.winner_user_address = player1.owner_address
                    else:
                        self.winner_user_address = player2.owner_address
                elif player1.choice == Choice.trick:
                    if player2.choice == Choice.block:
                        self.winner_user_address = player1.owner_address
                    else:
                        self.winner_user_address = player2.owner_address
                elif player1.choice == Choice.block:
                    if player2.choice == Choice.attack:
                        self.winner_user_address = player1.owner_address
                    else:
                        self.winner_user_address = player2.owner_address
