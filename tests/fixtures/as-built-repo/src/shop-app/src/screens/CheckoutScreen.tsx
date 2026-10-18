import { useState } from "react";
import { Button, Text, View } from "react-native";
import { ORDERS_PATH } from "../api/paths";
import { http } from "../api/http";

export function CheckoutScreen({ cart, navigation }) {
  const [error, setError] = useState<string | null>(null);

  async function placeOrder() {
    const response = await http.post(ORDERS_PATH, { items: cart.items });
    if (response.ok) {
      navigation.navigate("OrderPlaced", { id: response.body.id });
    } else {
      setError(response.body.message);
    }
  }

  return (
    <View>
      <Text>Review your order</Text>
      {error && <Text>{error}</Text>}
      <Button title="Place order" onPress={placeOrder} />
    </View>
  );
}
