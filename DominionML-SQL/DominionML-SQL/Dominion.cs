using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;

namespace DominionML_SQL
{
    public class Dominion
    {
        public static Dictionary<string, Card> Cards { get; private set; }

        static Dominion()
        {
            Cards = new Dictionary<string, Card>();
            // Base
            AddActionCard("Adventurer");
            AddActionCard("Bureaucrat", attack: true);
            AddActionCard("Cellar", draws: true);
            AddActionCard("Chancellor");
            AddActionCard("Chapel", trashes: true);
            AddActionCard("Council Room", draws: true, buys: true);
            AddActionCard("Feast");
            AddActionCard("Festival", actions: true, buys: true);
            AddVictoryCard("Gardens", "Gardens");
            AddActionCard("Laboratory", "Laboratories", draws: true);
            AddActionCard("Library", "Libraries", draws: true);
            AddActionCard("Market", buys: true);
            AddActionCard("Militia", attack: true);
            AddActionCard("Mine");
            AddActionCard("Moat", draws: true);
            AddActionCard("Moneylender");
            AddActionCard("Remodel", trashes: true);
            AddActionCard("Smithy", "Smithies", draws: true);
            AddActionCard("Spy", "Spies", attack: true);
            AddActionCard("Thief", "Thieves", attack: true);
            AddActionCard("Throne Room", actions: true, draws: true); // Not quite sure on this one, but Throne Room combined with lots of other cards can give you extra actions and draws, so I"ll count it. Better to round up.
            AddActionCard("Village", actions: true);
            AddActionCard("Witch", "Witches", draws: true, attack: true, curses: true);
            AddActionCard("Woodcutter", buys: true);
            AddActionCard("Workshop");

            // Intrigue
            AddActionCard("Baron", buys: true);
            AddActionCard("Bridge", buys: true);
            AddActionCard("Conspirator");
            AddActionCard("Coppersmith");
            AddActionCard("Courtyard", draws: true);
            AddVictoryCard("Duke");
            AddVictoryCard("Great Hall", action: true);
            AddVictoryCard("Harem", treasure: true);
            AddActionCard("Ironworks", "Ironworks");
            AddActionCard("Masquerade", draws: true);
            AddActionCard("Mining Village", actions: true);
            AddActionCard("Minion", draws: true, attack: true);
            AddVictoryCard("Nobles", "Nobles", action: true, actions: true, draws: true);
            AddActionCard("Pawn", buys: true);
            AddActionCard("Saboteur", attack: true);
            AddActionCard("Scout");
            AddActionCard("Secret Chamber");
            AddActionCard("Shanty Town", actions: true, draws: true);
            AddActionCard("Steward", draws: true, trashes: true);
            AddActionCard("Swindler", attack: true, curses: true); // Swindling Coppers can make you gain Curses, so this counts.
            AddActionCard("Torturer", draws: true, attack: true, curses: true);
            AddActionCard("Trading Post", trashes: true);
            AddActionCard("Tribute", actions: true, draws: true);
            AddActionCard("Upgrade", trashes: true);
            AddActionCard("Wishing Well", draws: true); // On this and cards like it, if it has the potential to give you more cards or actions than it took to play it, it counts as giving actions or draws. Chaining cards (Scout, Upgrade, etc.); don"t count, as they don"t let you have more than a single action or increase the size of your hand.

            // Seaside
            AddActionCard("Ambassador", attack: true, trashes: true); // Not quite truly trashing...but essentially the same idea. It gets cards out of your deck.
            AddActionCard("Bazaar", actions: true);
            AddActionCard("Caravan", draws: true);
            AddActionCard("Cutpurse", attack: true);
            AddActionCard("Embargo", "Embargoes");
            AddActionCard("Explorer");
            AddActionCard("Fishing Village", actions: true);
            AddActionCard("Ghost Ship", draws: true, attack: true);
            AddActionCard("Haven");
            AddVictoryCard("Island", action: true);
            AddActionCard("Lighthouse");
            AddActionCard("Lookout", trashes: true);
            AddActionCard("Merchant Ship");
            AddActionCard("Native Village", actions: true, draws: true);
            AddActionCard("Navigator");
            AddActionCard("Outpost");
            AddActionCard("Pearl Diver");
            AddActionCard("Pirate Ship", attack: true);
            AddActionCard("Salvager", buys: true, trashes: true);
            AddActionCard("Sea Hag", attack: true, curses: true);
            AddActionCard("Smugglers", "Smugglers");
            AddActionCard("Tactician", actions: true, buys: true, draws: true);
            AddActionCard("Treasure Map");
            AddActionCard("Treasury", "Treasuries");
            AddActionCard("Warehouse", draws: true); // This doesn"t let you have more cards in your hand, but it does let you draw and then choose what to discard, so it counts.
            AddActionCard("Wharf", "Wharves", draws: true, buys: true);

            // Alchemy
            AddActionCard("Alchemist", draws: true);
            AddActionCard("Apothecary", "Apothecaries");
            AddActionCard("Apprentice", draws: true, trashes: true);
            AddActionCard("Familiar", attack: true, curses: true);
            AddActionCard("Golem", actions: true); // It lets you play multiple actions in a single turn, so....I think I"ll try counting this here.
            AddActionCard("Herbalist");
            AddTreasureCard("Philosopher's Stone");
            AddActionCard("Possession");
            AddActionCard("Scrying Pool", draws: true, attack: true);
            AddActionCard("Transmute", trashes: true);
            AddActionCard("University", "Universities", actions: true);
            AddVictoryCard("Vineyard");

            // Prosperity
            AddTreasureCard("Bank");
            AddActionCard("Bishop", trashes: true);
            AddActionCard("City", "Cities", actions: true, draws: true);
            AddTreasureCard("Contraband", buys: true);
            AddActionCard("Counting House");
            AddActionCard("Expand", trashes: true);
            AddActionCard("Forge", trashes: true);
            AddActionCard("Goons", "Goons", buys: true, attack: true);
            AddActionCard("Grand Market", buys: true);
            AddTreasureCard("Hoard");
            AddActionCard("King's Court", actions: true, draws: true); // See my justification for Throne Room for this classification. Combining with +Actions and +Cards cards causes this to give both of them, so I"ll count this here to be safe.
            AddTreasureCard("Loan");
            AddActionCard("Mint");
            AddActionCard("Monument");
            AddActionCard("Mountebank", attack: true, curses: true);
            AddActionCard("Peddler");
            AddTreasureCard("Quarry", "Quarries");
            AddActionCard("Rabble", draws: true, attack: true);
            AddTreasureCard("Royal Seal");
            AddTreasureCard("Talisman");
            AddActionCard("Trade Route", buys: true, trashes: true);
            AddActionCard("Vault", draws: true);
            AddActionCard("Venture");
            AddActionCard("Watchtower", draws: true);
            AddActionCard("Worker's Village", actions: true);

            // Cornucopia
            AddVictoryCard("Fairgrounds", "Fairgrounds");
            AddActionCard("Farming Village", actions: true);
            AddActionCard("Fortune Teller", attack: true);
            AddActionCard("Hamlet", actions: true, buys: true);
            AddActionCard("Harvest");
            AddTreasureCard("Horn of Plenty", "Horns of Plenty");
            AddActionCard("Horse Traders", "Horse Traders", buys: true);
            AddActionCard("Hunting Party", "Hunting Parties", draws: true);
            AddActionCard("Jester", trashes: true, curses: true);
            AddActionCard("Menagerie", draws: true);
            AddActionCard("Remake", trashes: true);
            AddActionCard("Tournament"); // But at the same time...they aren"t common in the supply, so I"ll pass here...., actions: true, draws: true, buys: true, attack: true, curses: true); // This is because of the prizes that tournament brings with it. It isn"t an attack or anything, but its presence in the supply indicates that these things can appear.
            AddActionCard("Young Witch", "Young Witches", draws: true, attack: true, curses: true);
            // Prize Cards
            AddActionCard("Bag of Gold", supply: false, prize: true);
            AddTreasureCard("Diadem", supply: false, prize: true);
            AddActionCard("Followers", "Followers", draws: true, attack: true, curses: true, supply: false, prize: true);
            AddActionCard("Princess", "Princesses", buys: true, supply: false, prize: true);
            AddActionCard("Trusty Steed", draws: true, actions: true, supply: false, prize: true);

            // Hinterlands
            AddActionCard("Border Village", actions: true);
            AddTreasureCard("Cache");
            AddActionCard("Cartographer");
            AddActionCard("Crossroads", "Crossroads", actions: true, draws: true);
            AddActionCard("Develop", trashes: true);
            AddActionCard("Duchess", "Duchesses");
            AddActionCard("Embassy", "Embassies", draws: true);
            AddVictoryCard("Farmland", trashes: true);
            AddTreasureCard("Fool's Gold");
            AddActionCard("Haggler");
            AddActionCard("Highway", "Highways");
            AddTreasureCard("Ill-Gotten Gains", "Ill-Gotten Gains", curses: true);
            AddActionCard("Inn", actions: true, draws: true);
            AddActionCard("Jack of All Trades", "Jacks of All Trades", draws: true, trashes: true);
            AddActionCard("Mandarin");
            AddActionCard("Margrave", draws: true, buys: true, attack: true);
            AddActionCard("Noble Brigand", attack: true);
            AddActionCard("Nomad Camp", buys: true);
            AddActionCard("Oasis", "Oases");
            AddActionCard("Oracle", draws: true, attack: true);
            AddActionCard("Scheme");
            AddVictoryCard("Silk Road");
            AddActionCard("Spice Merchant", draws: true, buys: true);
            AddActionCard("Stables", "Stables", draws: true);
            AddActionCard("Trader", trashes: true);
            AddVictoryCard("Tunnel", action: true);

            // Basic Cards
            AddTreasureCard("Platinum");
            AddTreasureCard("Gold");
            AddTreasureCard("Silver");
            AddTreasureCard("Copper");
            AddTreasureCard("Potion");

            AddVictoryCard("Colony", "Colonies");
            AddVictoryCard("Province");
            AddVictoryCard("Duchy", "Duchies");
            AddVictoryCard("Estate");

            AddCard("Curse", curse: true);
            
            // Promo Cards (I don"t know if Stash is used, but the others are);
            AddTreasureCard("Stash", "Stashes");
            AddActionCard("Envoy", "Envoys", draws: true);
            AddActionCard("Governor", draws: true, trashes: true);
            AddActionCard("Walled Village", actions: true);
            AddActionCard("Black Market");
        }

        private static void AddCard(string name, string plural = null, bool action = false, bool victory = false, bool treasure = false, bool curse = false, bool actions = false, bool buys = false, bool draws = false, bool curses = false, bool trashes = false, bool attack = false, bool supply = true, bool prize = false)
        {
            Card card = new Card(name, plural, action, victory, treasure, curse, actions, buys, draws, curses, trashes, attack, supply, prize);
            Cards.Add(card.Name.Replace("'", "").Replace(' ', '_'), card);
        }

        private static void AddActionCard(string name, string plural = null, bool action = true, bool victory = false, bool treasure = false, bool curse = false, bool actions = false, bool buys = false, bool draws = false, bool curses = false, bool trashes = false, bool attack = false, bool supply = true, bool prize = false)
        {
            AddCard(name, plural, action, victory, treasure, curse, actions, buys, draws, curses, trashes, attack, supply, prize);
        }

        private static void AddVictoryCard(string name, string plural = null, bool action = false, bool victory = true, bool treasure = false, bool curse = false, bool actions = false, bool buys = false, bool draws = false, bool curses = false, bool trashes = false, bool attack = false, bool supply = true, bool prize = false)
        {
            AddCard(name, plural, action, victory, treasure, curse, actions, buys, draws, curses, trashes, attack, supply, prize);
        }

        private static void AddTreasureCard(string name, string plural = null, bool action = false, bool victory = false, bool treasure = true, bool curse = false, bool actions = false, bool buys = false, bool draws = false, bool curses = false, bool trashes = false, bool attack = false, bool supply = true, bool prize = false)
        {
            AddCard(name, plural, action, victory, treasure, curse, actions, buys, draws, curses, trashes, attack, supply, prize);
        }

        public static Card GetCard(string name)
        {
            //string key = Regex.Replace(name, @"[\W ]+", "").Replace(' ', '_');
            string key = name.Replace("'", "").Replace(' ', '_');
            if (Cards.ContainsKey(key))
            {
                return Cards[key];
            }
            else
            {
                return null;
            }
        }
    }

    public class Card
    {
        public string Name { get; private set; }
        public string Plural { get; private set; }

        public bool Action { get; private set; }
        public bool Victory { get; private set; }
        public bool Treasure { get; private set; }
        public bool Curse { get; private set; }

        public bool Actions { get; private set; }
        public bool Buys { get; private set; }
        public bool Draws { get; private set; }
        public bool Curses { get; private set; }
        public bool Trashes { get; private set; }
        public bool Attack { get; private set; }

        public bool Supply { get; private set; }
        public bool Prize { get; private set; }

        public Card(string name, string plural = null, bool action = false, bool victory = false, bool treasure = false, bool curse = false, bool actions = false, bool buys = false, bool draws = false, bool curses = false, bool trashes = false, bool attack = false, bool supply = true, bool prize = false)
        {
            Name = name;
            Plural = string.IsNullOrWhiteSpace(plural) ? name + 's' : plural;

            Action = action;
            Victory = victory;
            Treasure = treasure;
            Curse = curse;

            Actions = actions;
            Buys = buys;
            Draws = draws;
            Curses = curses;
            Trashes = trashes;
            Attack = attack;

            Supply = supply;
            Prize = prize;
        }
    }
}
