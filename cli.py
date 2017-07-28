import argparse, textwrap
from utils import *
import database as db
import bXcat, zXcat
from trades import *
from xcat import *
import ast

def save_state(trade):
    save(trade)
    db.create

def checkSellStatus(trade):
    if trade.buy.get_status() == 'funded':
        secret = get_secret()
        print("SECRET found in checksellactions", secret)
        trade = seller_redeem_p2sh(trade, secret)
        print("TRADE SUCCESSFULLY REDEEMED", trade)
        save_state(trade)
    elif trade.buy.get_status() == 'empty':
        print("Buyer has not yet funded the contract where you offered to buy {0}, please wait for them to complete their part.".format(trade.buy.currency))
    elif trade.buy.get_status() == 'redeemed':
        print("You have already redeemed the p2sh on the second chain of this trade.")

# TODO: function to calculate appropriate locktimes between chains
def checkBuyStatus(trade):
    if trade.sell.get_status() == 'funded' and trade.buy.get_status() != 'redeemed':
        print("One active trade available, fulfilling buyer contract...")
        # they should calculate redeemScript for themselves
        print("Trade commitment", trade.commitment)
        # TODO: which block to start computation from?
        htlc = create_htlc(trade.buy.currency, trade.buy.fulfiller, trade.buy.initiator, trade.commitment, trade.buy.locktime)
        buyer_p2sh = htlc['p2sh']
        print("Buyer p2sh:", buyer_p2sh)
        # If the two p2sh match...
        if buyer_p2sh == trade.buy.p2sh:
            fund_tx = fund_contract(trade.buy)
            trade.buy.fund_tx = fund_tx
            print("trade buy with redeemscript?", trade.buy.__dict__)
            save_state(trade)
        else:
            print("Compiled p2sh for htlc does not match what seller sent.")
    elif trade.buy.get_status() == 'redeemed':
        # TODO: secret parsing
        # secret = parse_secret(trade.buy.currency, trade.buy.redeem_tx)
        secret = get_secret()
        print("Found secret", secret)
        txid = auto_redeem_p2sh(trade.sell, secret)
        print("TXID after buyer redeem", txid)
        print("XCAT trade complete!")

def instantiateTrade(trade):
    return Trade(buy=Contract(trade['buy']), sell=Contract(trade['sell']))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
        description=textwrap.dedent('''\
                == Trades ==
                newtrade - create a new trade
                checktrades - check for actions to be taken on existing trades
                importtrade "hexstr" - import an existing trade from a hex string
                exporttrade - export the data of an existing xcat trade as a hex string
                findtrade - find a trade by the txid of the currency being traded out of

                '''))
    parser.add_argument("command", action="store", help="list commands")
    parser.add_argument("argument", action="store", nargs="*", help="add an argument")
    # parser.add_argument("--daemon", "-d", action="store_true", help="Run as daemon process")
    args = parser.parse_args()

    # how to hold state of role
    command = args.command
    if command == 'importtrade':
        hexstr = args.argument[0]
        trade = x2s(hexstr)
        trade = instantiateTrade(ast.literal_eval(trade))
        save_state(trade)
        # print(trade.toJ)
    elif command == 'exporttrade':
        trade = get_trade()
        hexstr = s2x(str(trade))
        print(trade)
        print(hexstr)
    elif command == 'checktrades':
        trade = get_trade()
        trade = instantiateTrade(trade)
        if find_role(trade.sell) == 'initiator':
            role = 'seller'
            checkSellStatus(trade)
        else:
            role = 'buyer'
            checkBuyStatus(trade)
    elif command == 'newtrade':
        erase_trade()
        role = 'seller'
        print("Creating new XCAT trade...")
        trade = seller_init(Trade())
        # Save it to leveldb
        db.create(trade)
    elif command == "daemon":
        #TODO: implement
        print("Run as daemon process")
    elif command == "findtrade":
        print("Finding trade")
        txid = args.argument[0]
        trade = db.get(txid)
        print(x2s(b2x(trade)))
    # Ad hoc testing starts here
    elif command == "step1":
        erase_trade()
        print("Creating new XCAT trade...")
        trade = seller_init(Trade())
        # Save it to leveldb
        save_state(trade)
    elif command == "step2":
        trade = get_trade()
        checkBuyStatus(trade)
    elif command == "step3":
        trade = get_trade()
        checkSellStatus(trade)
    elif command == "step4":
        trade = get_trade()
        checkBuyStatus(trade)
