import SwiftUI
import Combine

struct FoodChoice: Identifiable, Codable {
    let id: Int
    let title: String
    let image: String
    let cuisine: [String]
}

class FoodChoicesViewModel: ObservableObject {
    @Published var foodChoices: [FoodChoice] = []
    @Published var selectedFood: FoodChoice?

    private var cancellables = Set<AnyCancellable>()

    func fetchRandomFoodChoices() {
        guard let url = URL(string: "http://localhost:5000/random_food_choices") else { return }
        var request = URLRequest(url: url)
        request.addValue("Bearer \(your_access_token)", forHTTPHeaderField: "Authorization")

        URLSession.shared.dataTaskPublisher(for: request)
            .map { $0.data }
            .decode(type: [FoodChoice].self, decoder: JSONDecoder())
            .receive(on: DispatchQueue.main)
            .sink(receiveCompletion: { completion in
                switch completion {
                case .failure(let error):
                    print("Error: \(error)")
                case .finished:
                    break
                }
            }, receiveValue: { [weak self] foodChoices in
                self?.foodChoices = foodChoices
            })
            .store(in: &cancellables)
    }

   func selectFood(_ food: FoodChoice) {
    self.selectedFood = food

    guard let url = URL(string: "http://localhost:5000/store_choice") else { return }
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.addValue("Bearer \(your_access_token)", forHTTPHeaderField: "Authorization")
    request.addValue("application/json", forHTTPHeaderField: "Content-Type")

    let foodData = try? JSONEncoder().encode(food)
    request.httpBody = foodData

    URLSession.shared.dataTask(with: request) { data, response, error in
        if let error = error {
            print("Error: \(error)")
        } else {
            print("Choice stored successfully")
        }
    }.resume()
}

}

struct ContentView: View {
    @ObservedObject var viewModel = FoodChoicesViewModel()

    var body: some View {
        VStack {
            if viewModel.foodChoices.isEmpty {
                Text("Loading...")
                    .onAppear {
                        viewModel.fetchRandomFoodChoices()
                    }
            } else {
                ForEach(viewModel.foodChoices) { food in
                    VStack {
                        Text(food.title)
                        AsyncImage(url: URL(string: food.image)) { image in
                            image
                                .resizable()
                                .scaledToFit()
                        } placeholder: {
                            ProgressView()
                        }
                        .frame(width: 100, height: 100)
                        .onTapGesture {
                            viewModel.selectFood(food)
                        }
                    }
                }
            }
        }
    }
}
